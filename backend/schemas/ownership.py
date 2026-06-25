"""Schema for the ownership / shareholding-activity endpoints."""

from backend.schemas.common import APIModel


class OwnershipActivityRow(APIModel):
    symbol: str
    name: str
    metric: str                          # promoter | fii | dii | mf | insurance | banks | pension
    pct: float | None = None             # latest quarter
    prev_pct: float | None = None        # prior quarter
    change: float | None = None          # pp change QoQ (+ = accumulating)
    period: str | None = None            # e.g. "31-Mar-2026"
    prev_period: str | None = None


class OwnershipHistoryRow(APIModel):
    """One quarter of a stock's shareholding split (for trend charts)."""
    period: str | None = None
    promoter: float | None = None
    public: float | None = None
    fii: float | None = None
    dii: float | None = None
    mf: float | None = None
    insurance: float | None = None
    banks: float | None = None
    pension: float | None = None
