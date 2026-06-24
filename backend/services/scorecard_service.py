"""Composite stock scorecard — a glanceable multi-factor health check.

Scores a stock across six dimensions (valuation, growth, profitability,
financial health, red flags, momentum) entirely from data already in the DB —
financial statements, price history and the computed sentiment score — with no
external calls. Mirrors the "scorecard" pattern users expect from
Tickertape/Trendlyne. Ratios match backend.services.screener_service.
"""

from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Company, FinancialStatement, PriceHistory, SentimentScore
from backend.core.exceptions import NotFoundError
from backend.schemas.scorecard import ScorecardCheck, ScorecardOut

GOOD, AVG, BAD = 100, 50, 0
_VERDICT = {GOOD: "good", AVG: "average", BAD: "bad"}


def _ratio(a, b):
    return a / b if a is not None and b not in (None, 0) else None


def _growth(curr, prev):
    if curr is None or prev is None or prev <= 0:
        return None
    return (curr - prev) / prev


def _pct(x):
    return f"{x:+.0%}" if x is not None else "n/a"


def _num(x, fmt="{:.1f}"):
    return fmt.format(x) if x is not None else "n/a"


class ScorecardService:
    def compute(self, session: Session, symbol: str) -> ScorecardOut:
        symbol = symbol.upper()
        company = session.query(Company).filter_by(symbol=symbol).first()
        if not company:
            raise NotFoundError(f"Unknown symbol: {symbol}")

        rows = (
            session.query(FinancialStatement)
            .filter_by(company_id=company.id, period_type="annual")
            .order_by(FinancialStatement.period)
            .all()
        )
        latest = rows[-1] if rows else None
        prev = rows[-2] if len(rows) >= 2 else None

        price = (
            session.query(PriceHistory.close)
            .filter_by(company_id=company.id)
            .filter(PriceHistory.close.isnot(None))
            .order_by(PriceHistory.date.desc())
            .limit(1)
            .scalar()
        )
        cutoff = date.today() - timedelta(days=365)
        hi, lo = (
            session.query(func.max(PriceHistory.close), func.min(PriceHistory.close))
            .filter(PriceHistory.company_id == company.id, PriceHistory.date >= cutoff)
            .first()
        )
        sentiment = (
            session.query(SentimentScore.overall)
            .filter_by(symbol=symbol)
            .filter(SentimentScore.overall.isnot(None))
            .order_by(SentimentScore.date.desc())
            .limit(1)
            .scalar()
        )

        # --- derived ratios (same definitions as the screener) ---
        # yfinance often leaves per-share EPS null for Indian filers; derive it
        # from net income / shares when shares outstanding is available.
        eps = latest.eps if latest else None
        if (not eps) and latest and latest.shares_outstanding:
            eps = _ratio(latest.net_income, latest.shares_outstanding)
        pe = _ratio(price, eps) if (eps and eps > 0) else None
        book = _ratio(latest.total_equity, latest.shares_outstanding) if latest else None
        pb = _ratio(price, book) if (book and book > 0) else None
        roe = _ratio(latest.net_income, latest.total_equity) if latest else None
        cap_employed = (
            latest.total_assets - latest.current_liabilities
            if latest and latest.total_assets is not None and latest.current_liabilities is not None
            else None
        )
        roce = _ratio(latest.ebit, cap_employed) if latest else None
        npm = _ratio(latest.net_income, latest.revenue) if latest else None
        debt = (
            latest.total_liabilities - latest.current_liabilities
            if latest and latest.total_liabilities is not None and latest.current_liabilities is not None
            else None
        )
        de = _ratio(debt, latest.total_equity) if latest else None
        rev_g = _growth(latest.revenue, prev.revenue) if (latest and prev) else None
        profit_g = _growth(latest.net_income, prev.net_income) if (latest and prev) else None

        checks: list[ScorecardCheck] = []

        def add(category, score, detail):
            checks.append(ScorecardCheck(
                category=category, verdict=_VERDICT.get(score, "na"),
                score=score, detail=detail,
            ))

        # 1. Valuation
        if latest and (latest.net_income or 0) < 0:
            add("Valuation", BAD, "Loss-making — P/E not meaningful")
        elif pe is None:
            add("Valuation", None, "No P/E data available")
        else:
            pb_txt = f", P/B {pb:.1f}" if pb else ""
            if pe < 22 and (pb is None or pb < 4):
                add("Valuation", GOOD, f"Reasonably valued — P/E {pe:.1f}{pb_txt}")
            elif pe < 40:
                add("Valuation", AVG, f"Fairly valued — P/E {pe:.1f}{pb_txt}")
            else:
                add("Valuation", BAD, f"Expensive — P/E {pe:.1f}{pb_txt}")

        # 2. Growth (YoY)
        if rev_g is None and profit_g is None:
            add("Growth", None, "Insufficient history for growth")
        else:
            d = f"Revenue {_pct(rev_g)}, Profit {_pct(profit_g)} YoY"
            if (profit_g or -1) > 0.15 and (rev_g or -1) > 0.10:
                add("Growth", GOOD, f"Strong growth — {d}")
            elif (profit_g or -1) > 0 and (rev_g or -1) > 0:
                add("Growth", AVG, f"Moderate growth — {d}")
            else:
                add("Growth", BAD, f"Weak / declining — {d}")

        # 3. Profitability
        if roe is None and roce is None:
            add("Profitability", None, "No profitability data")
        else:
            d = f"ROE {_pct(roe)}, ROCE {_pct(roce)}, NPM {_pct(npm)}"
            if (roe or 0) > 0.15 and (roce or 0) > 0.15:
                add("Profitability", GOOD, f"Highly profitable — {d}")
            elif (roe or 0) > 0.10 or (roce or 0) > 0.10:
                add("Profitability", AVG, f"Decent returns — {d}")
            else:
                add("Profitability", BAD, f"Low returns — {d}")

        # 4. Financial health (leverage)
        if de is None:
            add("Financial Health", None, "No balance-sheet data")
        elif de < 0.5:
            add("Financial Health", GOOD, f"Low leverage — Debt/Equity {de:.2f}")
        elif de <= 1.0:
            add("Financial Health", AVG, f"Moderate leverage — Debt/Equity {de:.2f}")
        else:
            add("Financial Health", BAD, f"High leverage — Debt/Equity {de:.2f}")

        # 5. Red flags
        if not latest:
            add("Red Flags", None, "No financials to screen")
        else:
            flags = []
            if (latest.net_income or 0) < 0:
                flags.append("net loss")
            if de is not None and de > 1.5:
                flags.append("high leverage")
            if profit_g is not None and profit_g < 0:
                flags.append("falling profit")
            if (latest.total_equity or 0) <= 0:
                flags.append("negative net worth")
            n = len(flags)
            score = GOOD if n == 0 else (AVG if n == 1 else BAD)
            add("Red Flags", score,
                "No red flags detected" if not flags else "Flags: " + ", ".join(flags))

        # 6. Momentum / entry (blended sentiment, dampened if price near 52w high)
        pos = (price - lo) / (hi - lo) if (price and hi and lo and hi > lo) else None
        if sentiment is None:
            add("Momentum", None, "No sentiment computed yet")
        else:
            pos_txt = f", price at {pos:.0%} of 52w range" if pos is not None else ""
            score = GOOD if sentiment >= 60 else (AVG if sentiment >= 45 else BAD)
            if score == GOOD and pos is not None and pos > 0.9:
                score = AVG  # strong sentiment but overheated entry
            add("Momentum", score, f"Sentiment {sentiment:.0f}/100{pos_txt}")

        scored = [c.score for c in checks if c.score is not None]
        overall = round(sum(scored) / len(scored)) if scored else None
        if overall is None:
            rating = "Insufficient data"
        elif overall >= 75:
            rating = "Strong"
        elif overall >= 58:
            rating = "Good"
        elif overall >= 42:
            rating = "Average"
        else:
            rating = "Weak"

        return ScorecardOut(
            symbol=symbol, name=company.name,
            overall_score=overall, rating=rating, checks=checks,
        )


scorecard_service = ScorecardService()
