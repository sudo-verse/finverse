"""Schema for the earnings/results calendar."""

from datetime import date

from backend.schemas.common import APIModel


class ResultRow(APIModel):
    symbol: str
    name: str | None = None
    event_date: date
    detail: str | None = None
    # latest-FY fundamental context (we have no analyst estimates, so this is a
    # trend tag, not a vs-estimate beat/miss)
    fy: str | None = None
    pat_yoy: float | None = None
    revenue_yoy: float | None = None
    momentum: str | None = None
    tag: str | None = None        # Strong | Positive | Soft | Weak
