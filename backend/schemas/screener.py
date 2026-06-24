"""Schema for the stock screener (/api/screener)."""

from backend.schemas.common import APIModel


class ScreenerRow(APIModel):
    symbol: str
    name: str
    industry: str | None = None
    sector: str | None = None
    price: float | None = None
    market_cap: float | None = None      # price × shares (filing currency caveat)
    pe: float | None = None
    pb: float | None = None
    roe: float | None = None             # fractions
    roce: float | None = None
    npm: float | None = None
    debt_to_equity: float | None = None
    revenue_growth: float | None = None
    profit_growth: float | None = None
    sentiment: float | None = None       # latest snapshot, 0-100
    recommendation: str | None = None
