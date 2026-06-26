"""Schema for dividend analytics."""

from datetime import date

from backend.schemas.common import APIModel


class DividendRow(APIModel):
    symbol: str
    name: str | None = None
    amount: float | None = None       # ₹ per share (parsed)
    yield_pct: float | None = None    # amount / price
    event_date: date
    detail: str | None = None
    upcoming: bool = False
