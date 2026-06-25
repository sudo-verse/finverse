"""Schema for the sector-performance heatmap."""

from backend.schemas.common import APIModel


class SectorPerf(APIModel):
    name: str                            # short label, e.g. "Bank"
    index: str                           # NSE index name, e.g. "NIFTY BANK"
    last: float | None = None
    day: float | None = None             # % change today
    week: float | None = None            # % vs one week ago
    month: float | None = None           # % vs 30 days ago
    year: float | None = None            # % vs 365 days ago
    advances: int | None = None
    declines: int | None = None
    pe: float | None = None
