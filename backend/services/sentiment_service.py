"""AI Sentiment Intelligence engine.

Composes the existing layers into one explainable 0-100 score:

  Technical 30% ... app.analytics.technicals over DB price history
  Fundamental 30% . financial_statements rows (growth, returns, leverage, OCF)
  News 20% ........ NewsSignal rows (FinBERT labels, recency-weighted)
  Ownership 10% ... NSE shareholding pattern (promoter/FII/DII deltas)
  Market 10% ...... NIFTY trend + advance/decline breadth

Every pillar produces factor-level {score, status, explanation} entries, so
each recommendation can show *why*. Deterministic and rule-based on purpose:
fast, free, reproducible — the LLM layer stays in the Research Copilot.

Daily snapshots are persisted to sentiment_scores for the history chart.
"""

import logging
import time
from datetime import date

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.analytics import technicals as T
from app.analytics.analytics import load_prices
from app.db.database import engine, get_session
from app.db.models import Company, FinancialStatement, NewsSignal, SentimentScore
from backend.core.exceptions import NoDataError, NotFoundError
from backend.schemas.sentiment import (
    Factor,
    LeaderboardEntry,
    MomentumRange,
    NewsBucket,
    OwnershipRow,
    PillarDetail,
    PivotLevels,
    SentimentHistoryPoint,
    SentimentOut,
)

logger = logging.getLogger("finverse.api")

WEIGHTS = {"technical": 0.30, "fundamental": 0.30, "news": 0.20, "ownership": 0.10, "market": 0.10}

# (symbol) -> (ts, SentimentOut); full recompute is a few hundred ms + NSE calls
_CACHE: dict[str, tuple] = {}
CACHE_TTL = 600


def _band(score: float) -> str:
    if score >= 80:
        return "STRONG BUY"
    if score >= 60:
        return "BUY"
    if score >= 40:
        return "NEUTRAL"
    if score >= 20:
        return "SELL"
    return "STRONG SELL"


def _status(score: float) -> str:
    return "bullish" if score >= 60 else "bearish" if score < 40 else "neutral"


def _clamp(x: float) -> float:
    return max(0.0, min(100.0, x))


def _pillar(name: str, factors: list[Factor], summary_hint: str = "") -> PillarDetail:
    scored = [f for f in factors if f.score is not None]
    score = sum(f.score for f in scored) / len(scored) if scored else None
    lines = [f.explanation for f in scored[:4] if f.explanation]
    return PillarDetail(
        name=name,
        score=round(score, 1) if score is not None else None,
        status=_status(score) if score is not None else "no data",
        factors=factors,
        summary=" ".join(lines) or summary_hint or "Insufficient data for this pillar.",
    )


class SentimentService:
    # ------------------------------------------------------------- technical
    def technical(self, symbol: str) -> tuple[PillarDetail, list[MomentumRange], PivotLevels | None, dict]:
        df = load_prices(symbol)
        if df is None or df.empty or len(df) < 30:
            raise NoDataError(f"Not enough price history for {symbol}.")
        closes = df["close"].dropna()
        price = float(closes.iloc[-1])
        factors: list[Factor] = []

        r = T.rsi(closes)
        if r is not None:
            score = _clamp(100 - abs(r - 60) * 2.2) if r <= 70 else _clamp(100 - (r - 70) * 3)
            factors.append(Factor(
                name="RSI (14)", value=round(r, 1), score=round(score),
                status="bullish" if 55 <= r <= 70 else "bearish" if r < 40 else "overbought" if r > 70 else "neutral",
                explanation=f"RSI at {r:.1f} — " + (
                    "positive momentum without being overbought." if 55 <= r <= 70
                    else "overbought territory; pullback risk." if r > 70
                    else "weak momentum." if r < 40 else "neutral momentum."),
            ))

        m = T.macd(closes)
        if m:
            score = 75 if m["histogram"] > 0 else 30
            if m["crossover"] == "bullish":
                score = 85
            elif m["crossover"] == "bearish":
                score = 15
            factors.append(Factor(
                name="MACD", value=round(m["histogram"], 2), score=score,
                status=m["crossover"] or ("bullish" if m["histogram"] > 0 else "bearish"),
                explanation=(
                    f"Bullish MACD crossover within the last week." if m["crossover"] == "bullish"
                    else "Bearish MACD crossover within the last week." if m["crossover"] == "bearish"
                    else f"MACD histogram {'positive' if m['histogram'] > 0 else 'negative'} at {m['histogram']:.2f}."),
            ))

        mas = T.moving_average_levels(closes)
        above = [w for w in (20, 50, 200) if mas.get(f"sma{w}") and price > mas[f"sma{w}"]]
        cross = T.golden_cross(closes)
        ma_score = {0: 10, 1: 35, 2: 65, 3: 90}[len(above)]
        if cross == "golden":
            ma_score = min(100, ma_score + 10)
        elif cross == "death":
            ma_score = max(0, ma_score - 10)
        ma_expl = (
            f"Price above SMA{', SMA'.join(map(str, above))}." if above else "Price below all key SMAs."
        )
        if cross:
            ma_expl += f" {'Golden' if cross == 'golden' else 'Death'} cross detected (SMA50/SMA200)."
        factors.append(Factor(
            name="Moving Averages", value=len(above), score=ma_score,
            status="bullish" if len(above) >= 2 else "bearish", explanation=ma_expl,
        ))

        b = T.bollinger(closes)
        if b:
            pb = b["pct_b"]
            score = _clamp(pb * 100) if pb <= 0.95 else 40  # pinned to upper band = stretched
            factors.append(Factor(
                name="Bollinger Bands", value=round(pb, 2), score=round(score),
                status="bullish" if 0.5 <= pb <= 0.95 else "overbought" if pb > 0.95 else "bearish" if pb < 0.3 else "neutral",
                explanation=f"Price at {pb:.0%} of the Bollinger range" + (
                    " — riding the upper band." if pb > 0.95 else " — upper half, constructive." if pb >= 0.5 else " — lower half."),
            ))

        v = T.volume_trend(df)
        if v and v["ratio"] is not None:
            ratio = v["ratio"]
            trend_up = closes.tail(10).iloc[-1] >= closes.tail(10).iloc[0]
            score = 70 if (ratio > 1.15 and trend_up) else 30 if (ratio > 1.15 and not trend_up) else 50
            factors.append(Factor(
                name="Volume Trend", value=round(ratio, 2), score=score,
                status="bullish" if score >= 60 else "bearish" if score <= 40 else "neutral",
                explanation=f"10-day volume at {ratio:.2f}x the 50-day baseline"
                            + (" supporting the up-move." if score >= 60 else " on a falling price — distribution risk." if score <= 40 else "."),
            ))

        ranges = [MomentumRange(**x) for x in T.momentum_ranges(df)]
        mom_score = None
        if ranges:
            pos = [(x.current - x.low) / (x.high - x.low) for x in ranges if x.high > x.low]
            if pos:
                mom_score = _clamp(sum(pos) / len(pos) * 100)
                factors.append(Factor(
                    name="Momentum", value=round(mom_score), score=round(mom_score),
                    status=_status(mom_score),
                    explanation=f"Price sits at {mom_score:.0f}% of its recent ranges on average across 1W–1Y windows.",
                ))

        piv = T.pivot_points(df)
        pivots = PivotLevels(**piv) if piv else None
        return _pillar("Technical", factors), ranges, pivots, mas

    # ----------------------------------------------------------- fundamental
    def fundamental(self, session: Session, symbol: str) -> PillarDetail:
        company = session.query(Company).filter_by(symbol=symbol).first()
        if not company:
            raise NotFoundError(f"Unknown symbol: {symbol}")
        rows = (
            session.query(FinancialStatement)
            .filter_by(company_id=company.id, period_type="annual")
            .order_by(FinancialStatement.period).all()
        )
        factors: list[Factor] = []
        if len(rows) >= 2:
            latest, prev = rows[-1], rows[-2]

            def growth_factor(name, curr, prior, good=0.10):
                if curr is None or prior is None or prior <= 0:
                    return
                g = (curr - prior) / prior
                score = _clamp(50 + g / good * 25)
                factors.append(Factor(
                    name=name, value=round(g * 100, 1), score=round(score), status=_status(score),
                    explanation=f"{name} {'grew' if g >= 0 else 'fell'} {abs(g):.1%} YoY.",
                ))

            growth_factor("Revenue Growth", latest.revenue, prev.revenue)
            growth_factor("Profit Growth", latest.net_income, prev.net_income)

            def roe(r):
                return r.net_income / r.total_equity if r.net_income is not None and r.total_equity else None

            roe_now, roe_prev = roe(latest), roe(prev)
            if roe_now is not None:
                score = _clamp(roe_now / 0.20 * 70 + (10 if roe_prev is not None and roe_now > roe_prev else 0))
                factors.append(Factor(
                    name="ROE", value=round(roe_now * 100, 1), score=round(score), status=_status(score),
                    explanation=f"ROE at {roe_now:.1%}" + (
                        f", improving from {roe_prev:.1%}." if roe_prev is not None and roe_now > roe_prev
                        else f", down from {roe_prev:.1%}." if roe_prev is not None else "."),
                ))

            def de(r):
                if r.total_liabilities is None or r.current_liabilities is None or not r.total_equity:
                    return None
                return (r.total_liabilities - r.current_liabilities) / r.total_equity

            de_now, de_prev = de(latest), de(prev)
            if de_now is not None:
                score = _clamp(85 - de_now * 35)
                if de_prev is not None and de_now < de_prev:
                    score = _clamp(score + 10)
                factors.append(Factor(
                    name="Debt / Equity", value=round(de_now, 2), score=round(score), status=_status(score),
                    explanation=f"Debt-to-equity at {de_now:.2f}"
                                + (", declining YoY." if de_prev is not None and de_now < de_prev
                                   else ", rising YoY." if de_prev is not None and de_now > de_prev else "."),
                ))

            if latest.operating_cash_flow is not None and latest.net_income:
                conv = latest.operating_cash_flow / latest.net_income
                score = _clamp(40 + conv * 30)
                factors.append(Factor(
                    name="Cash Flow", value=round(conv, 2), score=round(score), status=_status(score),
                    explanation=f"Operating cash flow is {conv:.1f}x net profit — "
                                + ("healthy conversion." if conv >= 0.8 else "weak conversion."),
                ))
        return _pillar("Fundamental", factors,
                       summary_hint=f"No annual statements for {symbol} — run the financials ETL.")

    # ------------------------------------------------------------------ news
    def news(self, session: Session, symbol: str) -> tuple[PillarDetail, NewsBucket]:
        rows = (
            session.query(NewsSignal)
            .filter(NewsSignal.ticker == symbol)
            .order_by(NewsSignal.id.desc()).limit(50).all()
        )
        bucket = NewsBucket(positive_pct=0, negative_pct=0, neutral_pct=0, impact=None, count=len(rows))
        factors: list[Factor] = []
        if rows:
            n = len(rows)
            pos = sum(1 for r in rows if r.sentiment_label == "positive")
            neg = sum(1 for r in rows if r.sentiment_label == "negative")
            bucket.positive_pct = round(pos / n * 100, 1)
            bucket.negative_pct = round(neg / n * 100, 1)
            bucket.neutral_pct = round(100 - bucket.positive_pct - bucket.negative_pct, 1)

            # recency-weighted impact: newest signals count ~3x the oldest
            weighted = total = 0.0
            for i, r in enumerate(rows):
                w = 3.0 - 2.0 * i / max(n - 1, 1)
                s = (r.sentiment_score or 0.5) * (1 if r.sentiment_label == "positive" else -1 if r.sentiment_label == "negative" else 0)
                weighted += w * s
                total += w
            impact = weighted / total  # -1..1
            bucket.impact = round(impact, 3)
            score = _clamp(50 + impact * 50)
            factors.append(Factor(
                name="News Flow", value=bucket.positive_pct, score=round(score), status=_status(score),
                explanation=f"Of the last {n} signals, {bucket.positive_pct:.0f}% positive vs "
                            f"{bucket.negative_pct:.0f}% negative (recency-weighted impact {impact:+.2f}).",
            ))
            buys = sum(1 for r in rows[:15] if r.signal == "BUY")
            if buys:
                factors.append(Factor(
                    name="Engine Signals", value=buys, score=_clamp(50 + buys * 10), status="bullish",
                    explanation=f"{buys} BUY signal{'s' if buys > 1 else ''} among the 15 most recent engine events.",
                ))
        return _pillar("News", factors, summary_hint="No news signals recorded for this stock yet."), bucket

    # ------------------------------------------------------------- ownership
    def ownership(self, symbol: str) -> tuple[PillarDetail, list[OwnershipRow]]:
        factors: list[Factor] = []
        rows_out: list[OwnershipRow] = []
        try:
            from backend.services.nse_service import nse_service

            periods = nse_service.shareholding(symbol)
        except Exception as e:
            logger.warning("sentiment: shareholding unavailable for %s: %s", symbol, e)
            periods = []
        if len(periods) >= 2:
            latest, prev = periods[0], periods[1]
            prev_map = {h.category: h.pct for h in prev.holdings}
            for h in latest.holdings:
                delta = h.pct - prev_map[h.category] if h.pct is not None and prev_map.get(h.category) is not None else None
                rows_out.append(OwnershipRow(category=h.category, pct=h.pct, delta=delta))
                if delta is None:
                    continue
                cat = h.category.lower()
                if "promoter" in cat:
                    score = 80 if delta > 0.05 else 25 if delta < -0.25 else 60
                    factors.append(Factor(
                        name="Promoter Holding", value=h.pct, score=score, status=_status(score),
                        explanation=f"Promoter holding {'increased' if delta > 0.05 else 'decreased' if delta < -0.05 else 'stable'} "
                                    f"({delta:+.2f} pp QoQ at {h.pct:.2f}%).",
                    ))
                elif "foreign" in cat or "fii" in cat:
                    score = _clamp(55 + delta * 20)
                    factors.append(Factor(
                        name="FII Holding", value=h.pct, score=round(score), status=_status(score),
                        explanation=f"FII {'accumulation' if delta > 0 else 'reduction'} observed ({delta:+.2f} pp QoQ).",
                    ))
                elif "dii" in cat or "mutual" in cat or "institut" in cat:
                    score = _clamp(55 + delta * 20)
                    factors.append(Factor(
                        name="DII / MF Holding", value=h.pct, score=round(score), status=_status(score),
                        explanation=f"Domestic institutions {'added' if delta > 0 else 'trimmed'} ({delta:+.2f} pp QoQ).",
                    ))
        return _pillar("Ownership", factors,
                       summary_hint="Shareholding pattern unavailable from NSE right now."), rows_out

    # ---------------------------------------------------------------- market
    def market(self) -> PillarDetail:
        factors: list[Factor] = []
        try:
            from backend.services.nse_service import nse_service

            indices = nse_service.all_indices()
            nifty = next((i for i in indices if i.name == "NIFTY 50"), None)
            if nifty and nifty.perc_change is not None:
                score = _clamp(50 + nifty.perc_change * 15)
                factors.append(Factor(
                    name="NIFTY Trend", value=nifty.perc_change, score=round(score), status=_status(score),
                    explanation=f"NIFTY 50 {'up' if nifty.perc_change >= 0 else 'down'} {abs(nifty.perc_change):.2f}% today.",
                ))
            up = sum(1 for i in indices if (i.perc_change or 0) > 0)
            if indices:
                breadth = up / len(indices)
                score = _clamp(breadth * 100)
                factors.append(Factor(
                    name="Market Breadth", value=round(breadth * 100), score=round(score), status=_status(score),
                    explanation=f"{up} of {len(indices)} tracked indices are in the green.",
                ))
        except Exception as e:
            logger.warning("sentiment: market pillar unavailable: %s", e)
        return _pillar("Market", factors, summary_hint="Live market data unavailable — pillar excluded.")

    # ------------------------------------------------------------- composite
    def compute(self, session: Session, symbol: str, force: bool = False,
                skip_ownership: bool = False) -> SentimentOut:
        """Composite sentiment for one symbol.

        `skip_ownership=True` drops the per-symbol NSE shareholding call so a
        universe-wide pass (refresh_universe) stays DB-local and fast — ownership
        is only 10% and the weights renormalize over the pillars that have data.
        Such partial results bypass the per-symbol UI cache so the full
        on-demand computation stays authoritative there.
        """
        symbol = symbol.upper()
        if not skip_ownership:
            cached = _CACHE.get(symbol)
            if cached and not force and time.time() - cached[0] < CACHE_TTL:
                return cached[1]

        technical, ranges, pivots, mas = self.technical(symbol)
        fundamental = self.fundamental(session, symbol)
        news, bucket = self.news(session, symbol)
        if skip_ownership:
            ownership = _pillar("Ownership", [],
                                summary_hint="Ownership pillar skipped for bulk scoring.")
            holdings = []
        else:
            ownership, holdings = self.ownership(symbol)
        market = self.market()

        pillars = {"technical": technical, "fundamental": fundamental,
                   "news": news, "ownership": ownership, "market": market}
        # Re-normalize weights over pillars that actually have data, and use
        # data coverage as the confidence signal.
        live = {k: p for k, p in pillars.items() if p.score is not None}
        weight_sum = sum(WEIGHTS[k] for k in live) or 1.0
        overall = sum(WEIGHTS[k] * live[k].score for k in live) / weight_sum if live else 50.0
        confidence = sum(WEIGHTS[k] for k in live)

        reasons = sorted(
            (f for p in live.values() for f in p.factors if f.score is not None and f.score >= 60),
            key=lambda f: -f.score)[:6]
        risks = sorted(
            (f for p in live.values() for f in p.factors if f.score is not None and f.score <= 40),
            key=lambda f: f.score)[:4]

        out = SentimentOut(
            symbol=symbol,
            overall=round(overall, 1),
            recommendation=_band(overall),
            confidence=round(confidence, 2),
            pillars=list(pillars.values()),
            reasons=[r.explanation or r.name for r in reasons],
            risks=[r.explanation or r.name for r in risks],
            momentum=ranges,
            pivots=pivots,
            moving_averages={k: (round(v, 2) if v is not None else None) for k, v in mas.items()},
            news_bucket=bucket,
            holdings=holdings,
        )
        self._persist(out)
        if not skip_ownership:
            _CACHE[symbol] = (time.time(), out)
        return out

    @staticmethod
    def _persist(out: SentimentOut) -> None:
        try:
            SentimentScore.__table__.create(engine, checkfirst=True)
            by_name = {p.name.lower(): p.score for p in out.pillars}
            with get_session() as ws:
                row = ws.query(SentimentScore).filter_by(symbol=out.symbol, date=date.today()).first()
                if not row:
                    row = SentimentScore(symbol=out.symbol, date=date.today())
                    ws.add(row)
                row.overall, row.recommendation, row.confidence = out.overall, out.recommendation, out.confidence
                row.technical, row.fundamental = by_name.get("technical"), by_name.get("fundamental")
                row.news, row.ownership, row.market = by_name.get("news"), by_name.get("ownership"), by_name.get("market")
        except Exception:
            logger.exception("sentiment: failed to persist snapshot")

    def history(self, symbol: str, limit: int = 90) -> list[SentimentHistoryPoint]:
        SentimentScore.__table__.create(engine, checkfirst=True)
        with get_session() as ws:
            rows = (
                ws.query(SentimentScore).filter_by(symbol=symbol.upper())
                .order_by(SentimentScore.date.desc()).limit(limit).all()
            )
        rows.reverse()
        out = []
        prev = None
        for r in rows:
            reason = None
            if prev is not None and r.overall is not None and prev.overall is not None and abs(r.overall - prev.overall) >= 1:
                deltas = {
                    "technical": (r.technical or 0) - (prev.technical or 0),
                    "fundamental": (r.fundamental or 0) - (prev.fundamental or 0),
                    "news": (r.news or 0) - (prev.news or 0),
                    "ownership": (r.ownership or 0) - (prev.ownership or 0),
                    "market": (r.market or 0) - (prev.market or 0),
                }
                driver = max(deltas, key=lambda k: abs(deltas[k]))
                reason = f"{driver.capitalize()} score {'improved' if deltas[driver] > 0 else 'weakened'} ({deltas[driver]:+.0f})."
            out.append(SentimentHistoryPoint(
                date=str(r.date), overall=r.overall, technical=r.technical,
                fundamental=r.fundamental, news=r.news, ownership=r.ownership,
                market=r.market, recommendation=r.recommendation, reason=reason,
            ))
            prev = r
        return out

    # --------------------------------------------------------- leaderboard
    def leaderboard(self, session: Session, limit: int = 5, order: str = "top",
                    min_confidence: float = 0.0) -> list[LeaderboardEntry]:
        """Rank companies by their latest sentiment snapshot.

        Reads one row per symbol (the most recent date) from sentiment_scores,
        joins in company names, and returns the top/bottom `limit` by score.
        Coverage comes from refresh_universe()/the daily ETL snapshot.
        """
        SentimentScore.__table__.create(engine, checkfirst=True)
        with get_session() as ws:
            latest = (
                ws.query(SentimentScore.symbol,
                         func.max(SentimentScore.date).label("d"))
                .group_by(SentimentScore.symbol).subquery()
            )
            rows = (
                ws.query(SentimentScore)
                .join(latest, and_(SentimentScore.symbol == latest.c.symbol,
                                   SentimentScore.date == latest.c.d))
                .filter(SentimentScore.overall.isnot(None))
                .filter(SentimentScore.confidence >= min_confidence)
                .all()
            )
            # Snapshot the fields we need before the session closes.
            data = [
                (r.symbol, r.overall, r.recommendation, r.confidence,
                 r.technical, r.fundamental, r.news, str(r.date))
                for r in rows
            ]

        names = dict(session.query(Company.symbol, Company.name).all())
        data.sort(key=lambda t: t[1], reverse=(order != "bottom"))
        return [
            LeaderboardEntry(
                rank=i, symbol=sym, name=names.get(sym), overall=overall,
                recommendation=rec, confidence=conf, technical=tech,
                fundamental=fund, news=news, as_of=as_of,
            )
            for i, (sym, overall, rec, conf, tech, fund, news, as_of)
            in enumerate(data[:limit], start=1)
        ]

    def refresh_universe(self) -> dict:
        """Bulk-score every company so the leaderboard covers the universe.

        Skips the per-symbol NSE ownership call (skip_ownership) to stay fast;
        symbols without enough price history raise NoDataError and are skipped.
        Intended for the daily ETL and one-off backfills.
        """
        with get_session() as session:
            symbols = [c.symbol for c in
                       session.query(Company.symbol).order_by(Company.symbol).all()]
        scored = skipped = failed = 0
        for sym in symbols:
            try:
                with get_session() as session:
                    self.compute(session, sym, force=True, skip_ownership=True)
                scored += 1
            except (NoDataError, NotFoundError):
                skipped += 1
            except Exception:
                failed += 1
                logger.exception("sentiment: universe refresh failed for %s", sym)
        logger.info("sentiment: universe refresh — scored=%d skipped=%d failed=%d",
                    scored, skipped, failed)
        return {"scored": scored, "skipped": skipped, "failed": failed}


sentiment_service = SentimentService()
