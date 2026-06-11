"""Schemas for signal backtesting (/api/signals/performance)."""

from backend.schemas.common import APIModel


class SignalPerfRow(APIModel):
    signal: str                       # BUY | SELL
    count: int                        # signals with a forward window
    hit_rate: float | None = None     # fraction whose move matched direction
    avg_return_7d: float | None = None
    avg_return_30d: float | None = None


class SignalExample(APIModel):
    symbol: str | None
    signal: str
    date: str
    return_pct: float | None          # 30d when available, else 7d
    headline: str


class SignalPerformance(APIModel):
    evaluated: int
    rows: list[SignalPerfRow]
    best: list[SignalExample]
    worst: list[SignalExample]
