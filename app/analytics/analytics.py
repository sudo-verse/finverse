"""DB-backed analytics: read price_history and compute metrics per stock."""

import pandas as pd

from app.analytics import metrics
from app.db.database import get_session
from app.db.models import Company, PriceHistory


def load_prices(symbol: str) -> pd.DataFrame:
    """Return a date-indexed OHLCV DataFrame for a symbol (empty if none)."""
    with get_session() as session:
        company = session.query(Company).filter_by(symbol=symbol).first()
        if not company:
            return pd.DataFrame()

        rows = (
            session.query(
                PriceHistory.date, PriceHistory.open, PriceHistory.high,
                PriceHistory.low, PriceHistory.close, PriceHistory.volume,
            )
            .filter_by(company_id=company.id)
            .order_by(PriceHistory.date)
            .all()
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")


def analyze_symbol(symbol: str, risk_free=metrics.DEFAULT_RISK_FREE) -> dict:
    """Compute the full metric bundle for one symbol."""
    df = load_prices(symbol)
    if df.empty:
        return {"symbol": symbol, "error": "no price data"}

    result = metrics.compute_all(df["close"], risk_free=risk_free)
    result["symbol"] = symbol
    return result


def analyze_all(limit=None, risk_free=metrics.DEFAULT_RISK_FREE):
    """Compute metrics for every company that has price data."""
    with get_session() as session:
        q = session.query(Company.symbol).order_by(Company.symbol)
        if limit:
            q = q.limit(limit)
        symbols = [s for (s,) in q.all()]

    results = []
    for sym in symbols:
        r = analyze_symbol(sym, risk_free=risk_free)
        if "error" not in r:
            results.append(r)
    return results
