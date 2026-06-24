"""Stock endpoints — composes the existing analytics layers:

  - price series + SMAs ............ app.analytics.analytics.load_prices
                                     + app.analytics.metrics.moving_average
  - quant bundle (returns, vol,
    Sharpe, drawdown, trend) ....... app.analytics.metrics.compute_all
  - fundamentals ................... app.analytics.financial_analysis.analyze_symbol
  - recent signals ................. news_signals table

No metric is recomputed here; the service only assembles and shapes.
"""

import logging
import math

from sqlalchemy.orm import Session

from app.analytics import metrics as M
from app.analytics.analytics import load_prices
from app.analytics.financial_analysis import analyze_symbol as fin_analyze
from app.db.models import Company, NewsSignal
from backend.core.exceptions import NoDataError, NotFoundError
from backend.schemas.signal import SignalOut
from backend.schemas.stock import (
    CompanyOut,
    Fundamentals,
    PricePoint,
    QuantMetrics,
    StockDetailOut,
)
from backend.services.signal_service import base_signal_query, row_to_signal

logger = logging.getLogger("finverse.api")

TRADING_DAYS_52W = 252
RECENT_SIGNALS_LIMIT = 10
TREND_TO_RECOMMENDATION = {
    "uptrend": "BUY",
    "downtrend": "SELL",
    "sideways": "HOLD",
    "insufficient_data": "HOLD",
}


def _clean(x: float | None) -> float | None:
    """NaN-safe float for JSON."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return float(x)


class StockService:
    def list_companies(
        self, session: Session, search: str | None = None, limit: int = 1000
    ) -> list[CompanyOut]:
        q = session.query(Company).order_by(Company.symbol)
        if search:
            like = f"%{search.strip()}%"
            q = q.filter((Company.symbol.ilike(like)) | (Company.name.ilike(like)))
        return [
            CompanyOut(
                symbol=c.symbol,
                name=c.name,
                industry=c.industry,
                sector=c.sector or c.industry,
                isin=c.isin,
            )
            for c in q.limit(limit).all()
        ]

    def get_stock_detail(
        self, session: Session, symbol: str, history_days: int = 365
    ) -> StockDetailOut:
        symbol = symbol.upper()
        company = session.query(Company).filter_by(symbol=symbol).first()
        if not company:
            raise NotFoundError(f"Unknown symbol: {symbol}")

        df = load_prices(symbol)
        if df.empty:
            raise NoDataError(
                f"No price history for {symbol}. Run the ETL: python -m app.etl.run_etl"
            )

        closes = df["close"]

        # --- SMA overlays on the full series (same as the Streamlit chart) ---
        out = df.copy()
        for w in (20, 50, 200):
            if len(df) >= w:
                out[f"sma{w}"] = M.moving_average(closes, w, "sma")
        history = out.tail(history_days)
        price_history = [
            PricePoint(
                date=idx.date(),
                open=_clean(row.get("open")),
                high=_clean(row.get("high")),
                low=_clean(row.get("low")),
                close=_clean(row.get("close")),
                volume=int(row["volume"]) if _clean(row.get("volume")) is not None else None,
                sma20=_clean(row.get("sma20")),
                sma50=_clean(row.get("sma50")),
                sma200=_clean(row.get("sma200")),
            )
            for idx, row in history.iterrows()
        ]

        # --- Quant bundle (L4) ---
        quant_raw = M.compute_all(closes)
        quant = QuantMetrics(**{k: quant_raw.get(k) for k in QuantMetrics.model_fields})

        # --- Fundamentals (L5) — optional, depends on financials ETL ---
        fin_raw = fin_analyze(symbol)
        fundamentals = (
            Fundamentals(**{k: fin_raw.get(k) for k in Fundamentals.model_fields})
            if "error" not in fin_raw
            else None
        )

        # --- Day change + 52-week range (presentation glue from the series) ---
        # Live feeds can leave the most recent bar with a NaN close (partial
        # trading day), so quote off the last bar that actually has one.
        valid = df[df["close"].notna()]
        if valid.empty:
            raise NoDataError(f"No usable closing prices for {symbol}.")
        last = valid.iloc[-1]
        prev_close = float(valid["close"].iloc[-2]) if len(valid) >= 2 else None
        price = _clean(last["close"])
        change = (price - prev_close) if (price is not None and prev_close) else None
        window_52w = closes.tail(TRADING_DAYS_52W)

        # --- Recommendation: latest engine signal, else SMA trend (L4) ---
        recent_rows = (
            base_signal_query(session)
            .filter(NewsSignal.ticker == symbol)
            .order_by(NewsSignal.id.desc())
            .limit(RECENT_SIGNALS_LIMIT)
            .all()
        )
        recent_signals: list[SignalOut] = [row_to_signal(r) for r in recent_rows]
        if recent_signals:
            recommendation = recent_signals[0].signal
            confidence = recent_signals[0].confidence
        else:
            recommendation = TREND_TO_RECOMMENDATION.get(quant.trend or "", "HOLD")
            confidence = None

        return StockDetailOut(
            symbol=symbol,
            name=company.name,
            industry=company.industry,
            price=price,
            change=change,
            change_pct=(change / prev_close) if (change is not None and prev_close) else None,
            day_high=_clean(last.get("high")),
            day_low=_clean(last.get("low")),
            week52_high=_clean(window_52w.max()),
            week52_low=_clean(window_52w.min()),
            recommendation=recommendation,
            recommendation_confidence=confidence,
            quant=quant,
            fundamentals=fundamentals,
            price_history=price_history,
            recent_signals=recent_signals,
        )


stock_service = StockService()
