"""Schemas for the earnings-growth (momentum) tracker.

All financials we hold are annual (FY), so growth is year-over-year and
"momentum" is this year's PAT growth versus last year's — accelerating,
decelerating or steady. Growth values are fractions (0.062 = +6.2%); the
frontend renders the percentage.
"""

from backend.schemas.common import APIModel


class EarningsYear(APIModel):
    """One fiscal year for a single company (stock-page detail)."""
    fy: str
    revenue: float | None = None
    net_income: float | None = None
    eps: float | None = None
    revenue_yoy: float | None = None
    pat_yoy: float | None = None
    net_margin: float | None = None


class EarningsRow(APIModel):
    """A company's latest-year growth snapshot (tracker table)."""
    symbol: str
    name: str
    fy: str
    revenue: float | None = None
    net_income: float | None = None
    eps: float | None = None
    revenue_yoy: float | None = None
    pat_yoy: float | None = None
    eps_yoy: float | None = None
    net_margin: float | None = None
    margin_delta: float | None = None      # percentage-point change vs prior year
    momentum: str | None = None            # "accelerating" | "decelerating" | "steady"
    trend: list[float] = []                # trailing net-income series (sparkline)


class StockEarnings(APIModel):
    """Full annual history for one stock (stock-page panel)."""
    symbol: str
    name: str
    fy: str | None = None
    revenue_yoy: float | None = None
    pat_yoy: float | None = None
    momentum: str | None = None
    years: list[EarningsYear] = []
