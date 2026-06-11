"""Stock screener — one computed row per company across the NIFTY-500
universe (fundamental ratios + growth + valuation + latest sentiment).

Built as set-based SQL + a single Python pass (no per-symbol pandas), then
cached in memory for 10 minutes. Filtering/sorting happens client-side —
500 rows is nothing for the browser and keeps the API surface simple.

Caveat carried over from the data layer: yfinance reports statements in each
company's filing currency, so PE/PB are unreliable for the few USD filers;
ratios and growth are currency-agnostic.
"""

import time

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Company, FinancialStatement, PriceHistory, SentimentScore
from backend.schemas.screener import ScreenerRow

_cache: tuple[float, list[ScreenerRow]] | None = None
CACHE_TTL = 600


def _latest_prices(session: Session) -> dict[int, float]:
    """company_id -> latest close (one grouped query, not 500)."""
    latest_date = (
        session.query(PriceHistory.company_id, func.max(PriceHistory.date).label("d"))
        .group_by(PriceHistory.company_id).subquery()
    )
    rows = (
        session.query(PriceHistory.company_id, PriceHistory.close)
        .join(latest_date, (PriceHistory.company_id == latest_date.c.company_id)
              & (PriceHistory.date == latest_date.c.d))
        .all()
    )
    return {cid: close for cid, close in rows if close is not None}


def _latest_sentiment(session: Session) -> dict[str, tuple[float, str]]:
    latest = (
        session.query(SentimentScore.symbol, func.max(SentimentScore.date).label("d"))
        .group_by(SentimentScore.symbol).subquery()
    )
    rows = (
        session.query(SentimentScore.symbol, SentimentScore.overall, SentimentScore.recommendation)
        .join(latest, (SentimentScore.symbol == latest.c.symbol)
              & (SentimentScore.date == latest.c.d))
        .all()
    )
    return {sym: (score, rec) for sym, score, rec in rows if score is not None}


def _build(session: Session) -> list[ScreenerRow]:
    prices = _latest_prices(session)
    sentiment = _latest_sentiment(session)

    fins: dict[int, list[FinancialStatement]] = {}
    for f in (
        session.query(FinancialStatement)
        .filter_by(period_type="annual")
        .order_by(FinancialStatement.company_id, FinancialStatement.period)
        .all()
    ):
        fins.setdefault(f.company_id, []).append(f)

    def ratio(a, b):
        return a / b if a is not None and b else None

    def growth(curr, prev):
        if curr is None or prev is None or prev <= 0:
            return None
        return (curr - prev) / prev

    out = []
    for c in session.query(Company).order_by(Company.symbol).all():
        rows = fins.get(c.id, [])
        latest = rows[-1] if rows else None
        prev = rows[-2] if len(rows) >= 2 else None
        price = prices.get(c.id)

        eps = latest.eps if latest else None
        book = ratio(latest.total_equity, latest.shares_outstanding) if latest else None
        debt = None
        if latest and latest.total_liabilities is not None and latest.current_liabilities is not None:
            debt = latest.total_liabilities - latest.current_liabilities
        cap_emp = None
        if latest and latest.total_assets is not None and latest.current_liabilities is not None:
            cap_emp = latest.total_assets - latest.current_liabilities

        sent = sentiment.get(c.symbol)
        out.append(ScreenerRow(
            symbol=c.symbol,
            name=c.name,
            industry=c.industry,
            price=price,
            market_cap=(price * latest.shares_outstanding
                        if price is not None and latest and latest.shares_outstanding else None),
            pe=ratio(price, eps) if eps and eps > 0 else None,
            pb=ratio(price, book) if book and book > 0 else None,
            roe=ratio(latest.net_income, latest.total_equity) if latest else None,
            roce=ratio(latest.ebit, cap_emp) if latest else None,
            npm=ratio(latest.net_income, latest.revenue) if latest else None,
            debt_to_equity=ratio(debt, latest.total_equity) if latest else None,
            revenue_growth=growth(latest.revenue, prev.revenue) if latest and prev else None,
            profit_growth=growth(latest.net_income, prev.net_income) if latest and prev else None,
            sentiment=sent[0] if sent else None,
            recommendation=sent[1] if sent else None,
        ))
    return out


def screen(session: Session) -> list[ScreenerRow]:
    global _cache
    if _cache and time.time() - _cache[0] < CACHE_TTL:
        return _cache[1]
    rows = _build(session)
    _cache = (time.time(), rows)
    return rows
