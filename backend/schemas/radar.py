"""Schema for the 52-week high/low radar."""

from backend.schemas.common import APIModel


class RadarRow(APIModel):
    symbol: str
    name: str
    band: str                            # "high" | "low"
    price: float | None = None
    high52: float | None = None
    low52: float | None = None
    pct_from_high: float | None = None   # ≤0 (0 = at high)
    pct_from_low: float | None = None    # ≥0 (0 = at low)
    pct_in_range: float | None = None    # 0 (at low) … 100 (at high)


class StockRange(APIModel):
    """One stock's position in its 52-week range (for the stock page)."""
    symbol: str
    price: float | None = None
    high52: float | None = None
    low52: float | None = None
    pct_from_high: float | None = None
    pct_from_low: float | None = None
    pct_in_range: float | None = None
    at_high: bool = False                # within 1% of the 52w high
    at_low: bool = False
