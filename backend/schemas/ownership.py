"""Schema for the ownership / shareholding-activity endpoints."""

from backend.schemas.common import APIModel


class OwnershipActivityRow(APIModel):
    symbol: str
    name: str
    metric: str                          # "promoter" | "fii" | "dii"
    pct: float | None = None             # latest quarter
    prev_pct: float | None = None        # prior quarter
    change: float | None = None          # pp change QoQ (+ = accumulating)
    period: str | None = None            # e.g. "31-Mar-2026"
    prev_period: str | None = None
