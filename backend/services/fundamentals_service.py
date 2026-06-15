"""Company-terminal service: financial statements, ratio trends, CAGR,
long-range price history and AI pros/cons.

Data sources, in keeping with "reuse, don't duplicate":
  - financial_statements table (populated by app.etl.financials_etl / yfinance)
  - price_history table for <=1Y ranges; yfinance directly for longer ranges
    (the DB only stores 1 year — backfilling 10y x 500 symbols isn't worth it)
  - app.genai.report_generator.build_context + Gemini for pros/cons,
    cached in the company_insights table
"""

import json
import logging
import re
import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.analytics import metrics as M
from app.db.database import engine, get_session
from app.db.models import Company, CompanyInsight, FinancialStatement
from app.genai import gemini_client
from backend.core.exceptions import NoDataError, NotFoundError, ServiceUnavailableError
from backend.schemas.stock import (
    CagrRow,
    PricePoint,
    ProsConsItem,
    ProsConsOut,
    RatioPoint,
    StatementRow,
)

logger = logging.getLogger("finverse.api")

RANGE_DAYS = {"1M": 22, "6M": 126, "1Y": 252, "3Y": 756, "5Y": 1260, "10Y": 2520, "MAX": None}
YF_PERIOD = {"3Y": "3y", "5Y": "5y", "10Y": "10y", "MAX": "max"}

# (symbol, range) -> (fetched_at, points); yfinance daily bars barely change intraday
_HISTORY_CACHE: dict[tuple, tuple] = {}
HISTORY_TTL = 3600


def _company(session: Session, symbol: str) -> Company:
    company = session.query(Company).filter_by(symbol=symbol).first()
    if not company:
        raise NotFoundError(f"Unknown symbol: {symbol}")
    return company


def _growth(curr, prev):
    if curr is None or prev is None or prev == 0:
        return None
    if prev < 0:  # growth off a negative base is meaningless
        return None
    return (curr - prev) / prev


def _statement_rows(session: Session, company_id: int) -> list[FinancialStatement]:
    return (
        session.query(FinancialStatement)
        .filter_by(company_id=company_id, period_type="annual")
        .order_by(FinancialStatement.period)
        .all()
    )


class FundamentalsService:
    # ----------------------------------------------------------- statements
    def statements(self, session: Session, symbol: str) -> list[StatementRow]:
        company = _company(session, symbol)
        rows = _statement_rows(session, company.id)
        if not rows:
            raise NoDataError(
                f"No financial statements for {symbol} yet — "
                "run `python -m app.etl.financials_etl`."
            )
        out: list[StatementRow] = []
        prev = None
        for r in rows:
            out.append(StatementRow(
                period=r.period,
                revenue=r.revenue,
                net_income=r.net_income,
                ebit=r.ebit,
                eps=r.eps,
                total_assets=r.total_assets,
                total_equity=r.total_equity,
                total_liabilities=r.total_liabilities,
                operating_cash_flow=r.operating_cash_flow,
                revenue_growth=_growth(r.revenue, prev.revenue if prev else None),
                net_income_growth=_growth(r.net_income, prev.net_income if prev else None),
                eps_growth=_growth(r.eps, prev.eps if prev else None),
            ))
            prev = r
        return out

    # --------------------------------------------------------------- ratios
    def ratios(self, session: Session, symbol: str) -> list[RatioPoint]:
        company = _company(session, symbol)
        rows = _statement_rows(session, company.id)
        if not rows:
            raise NoDataError(f"No financial statements for {symbol} yet.")
        out = []
        for r in rows:
            equity = r.total_equity or None
            capital_employed = (
                (r.total_assets - r.current_liabilities)
                if r.total_assets is not None and r.current_liabilities is not None
                else None
            )
            debt = (
                (r.total_liabilities - r.current_liabilities)
                if r.total_liabilities is not None and r.current_liabilities is not None
                else None
            )
            out.append(RatioPoint(
                period=r.period,
                roe=(r.net_income / equity) if r.net_income is not None and equity else None,
                roce=(r.ebit / capital_employed) if r.ebit is not None and capital_employed else None,
                opm=(r.ebit / r.revenue) if r.ebit is not None and r.revenue else None,
                npm=(r.net_income / r.revenue) if r.net_income is not None and r.revenue else None,
                debt_to_equity=(debt / equity) if debt is not None and equity else None,
            ))
        return out

    # ----------------------------------------------------------------- CAGR
    def cagr(self, session: Session, symbol: str) -> list[CagrRow]:
        company = _company(session, symbol)
        rows = _statement_rows(session, company.id)

        def series(getter):
            return [(int(re.sub(r"\D", "", r.period)), getter(r)) for r in rows
                    if getter(r) is not None and re.search(r"\d{4}", r.period)]

        def cagr_over(points, years):
            """CAGR between the latest point and the one `years` earlier."""
            if not points:
                return None
            by_year = dict(points)
            end_year = max(by_year)
            start_year = end_year - years
            if start_year not in by_year:
                return None
            start, end = by_year[start_year], by_year[end_year]
            if start is None or end is None or start <= 0 or end <= 0:
                return None
            return (end / start) ** (1 / years) - 1

        metrics = [
            ("Sales", series(lambda r: r.revenue)),
            ("Profit", series(lambda r: r.net_income)),
            ("EPS", series(lambda r: r.eps)),
            ("ROE", series(lambda r: (r.net_income / r.total_equity)
                           if r.net_income is not None and r.total_equity else None)),
        ]
        out = [
            CagrRow(metric=name,
                    y1=cagr_over(pts, 1), y3=cagr_over(pts, 3),
                    y5=cagr_over(pts, 5), y10=cagr_over(pts, 10))
            for name, pts in metrics
        ]

        # Price CAGR from the long-range history (yfinance, cached)
        try:
            points = self.history(session, symbol, "MAX")
            closes = [(p.date, p.close) for p in points if p.close is not None]
            price_row = CagrRow(metric="Price")
            if closes:
                last_date, last = closes[-1]
                for years, field in ((1, "y1"), (3, "y3"), (5, "y5"), (10, "y10")):
                    target = last_date.replace(year=last_date.year - years)
                    older = [c for d, c in closes if d <= target]
                    if older and older[-1] > 0 and last > 0:
                        setattr(price_row, field, (last / older[-1]) ** (1 / years) - 1)
            out.append(price_row)
        except Exception as e:
            logger.warning("cagr: price leg failed for %s: %s", symbol, e)
            out.append(CagrRow(metric="Price"))
        return out

    # -------------------------------------------------------------- history
    def history(self, session: Session, symbol: str, range_key: str) -> list[PricePoint]:
        range_key = range_key.upper()
        if range_key not in RANGE_DAYS:
            raise NoDataError(f"Unknown range '{range_key}' — use {', '.join(RANGE_DAYS)}.")
        _company(session, symbol)

        cached = _HISTORY_CACHE.get((symbol, range_key))
        if cached and time.time() - cached[0] < HISTORY_TTL:
            return cached[1]

        if range_key in YF_PERIOD:
            df = self._yf_history(symbol, YF_PERIOD[range_key])
        else:
            from app.analytics.analytics import load_prices

            df = load_prices(symbol)
        if df is None or df.empty:
            raise NoDataError(f"No price history for {symbol} ({range_key}).")

        closes = df["close"]
        for w in (20, 50, 200):
            if len(closes) >= w:
                df[f"sma{w}"] = M.moving_average(closes, w, "sma")
        days = RANGE_DAYS[range_key]
        if days:
            df = df.tail(days)

        def _clean(v):
            return None if v is None or (isinstance(v, float) and v != v) else v

        points = [
            PricePoint(
                date=idx.date() if hasattr(idx, "date") else idx,
                close=_clean(row.get("close")),
                volume=_clean(row.get("volume")),
                sma20=_clean(row.get("sma20")),
                sma50=_clean(row.get("sma50")),
                sma200=_clean(row.get("sma200")),
            )
            for idx, row in df.iterrows()
        ]
        _HISTORY_CACHE[(symbol, range_key)] = (time.time(), points)
        return points

    @staticmethod
    def _yf_history(symbol: str, period: str):
        import yfinance as yf

        df = yf.Ticker(f"{symbol}.NS").history(period=period, interval="1d", auto_adjust=True)
        if df is None or df.empty:
            return None
        df = df.rename(columns={"Close": "close", "Volume": "volume"})
        df.index = df.index.tz_localize(None)
        return df[["close", "volume"]]

    # ------------------------------------------------------------ pros/cons
    PROS_CONS_SYSTEM = (
        "You are an equity research analyst. From the structured data, produce "
        "a balanced pros/cons assessment like Screener.in. Return STRICT JSON "
        'only: {"pros": [{"point": str, "confidence": float}], '
        '"cons": [{"point": str, "confidence": float}]} with 3-6 items each, '
        "confidence 0..1 reflecting how strongly the data supports the point. "
        "Every point must be grounded in the provided data — quote figures. "
        "No markdown, no commentary outside the JSON."
    )

    def pros_cons(self, session: Session, symbol: str, refresh: bool = False) -> ProsConsOut:
        _company(session, symbol)
        CompanyInsight.__table__.create(engine, checkfirst=True)

        if not refresh:
            row = (
                session.query(CompanyInsight)
                .filter_by(symbol=symbol, kind="pros_cons")
                .first()
            )
            if row and row.content:
                data = json.loads(row.content)
                return ProsConsOut(
                    symbol=symbol, cached=True, model=row.model,
                    generated_at=str(row.generated_at),
                    pros=[ProsConsItem(**p) for p in data.get("pros", [])],
                    cons=[ProsConsItem(**c) for c in data.get("cons", [])],
                )
            # No cache and not an explicit refresh — return empty instead of
            # auto-generating, so merely viewing the page never spends an AI
            # call. Generation happens only on the user's Generate click
            # (refresh=true).
            return ProsConsOut(symbol=symbol, cached=False, pros=[], cons=[])

        if not gemini_client.is_configured():
            raise ServiceUnavailableError("GEMINI_API_KEY is not configured.")
        from app.config import GEMINI_MODEL
        from app.genai.report_generator import build_context

        context = build_context(symbol)
        prompt = (
            f"Company: {context['company']} ({symbol}) on the NSE.\n\n"
            f"=== STRUCTURED DATA ===\n{json.dumps(context, default=str)[:9000]}\n\n"
            f"JSON:"
        )
        raw = gemini_client.generate_text(prompt, system_instruction=self.PROS_CONS_SYSTEM)
        match = re.search(r"\{.*\}", raw or "", re.DOTALL)
        if not match:
            raise NoDataError(f"Could not generate pros/cons for {symbol}.")
        data = json.loads(match.group(0))
        data = {
            "pros": [p for p in data.get("pros", []) if p.get("point")][:6],
            "cons": [c for c in data.get("cons", []) if c.get("point")][:6],
        }

        # upsert the cache row (separate session: request session is read-mostly)
        with get_session() as ws:
            row = ws.query(CompanyInsight).filter_by(symbol=symbol, kind="pros_cons").first()
            if row:
                row.content, row.model, row.generated_at = json.dumps(data), GEMINI_MODEL, datetime.utcnow()
            else:
                ws.add(CompanyInsight(symbol=symbol, kind="pros_cons",
                                      content=json.dumps(data), model=GEMINI_MODEL))

        return ProsConsOut(
            symbol=symbol, cached=False, model=GEMINI_MODEL,
            generated_at=str(datetime.utcnow()),
            pros=[ProsConsItem(point=p["point"], confidence=float(p.get("confidence", 0.5))) for p in data["pros"]],
            cons=[ProsConsItem(point=c["point"], confidence=float(c.get("confidence", 0.5))) for c in data["cons"]],
        )


fundamentals_service = FundamentalsService()
