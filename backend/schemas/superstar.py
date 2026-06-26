"""Schema for the marquee-investor ("superstar") activity tracker."""

from datetime import date

from backend.schemas.common import APIModel


class SuperstarTrade(APIModel):
    symbol: str | None = None
    name: str | None = None
    side: str | None = None              # BUY | SELL
    value: float | None = None
    deal_date: date
    deal_type: str | None = None         # bulk | block | sast


class SuperstarRow(APIModel):
    investor: str
    kind: str                            # Investor | Fund
    num_trades: int
    buy_value: float = 0.0
    sell_value: float = 0.0
    last_active: date | None = None
    stocks: list[str] = []
    trades: list[SuperstarTrade] = []
