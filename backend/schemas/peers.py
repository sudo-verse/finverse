"""Schema for the peer-comparison endpoint."""

from backend.schemas.common import APIModel


class PeerRow(APIModel):
    symbol: str
    name: str
    is_target: bool = False
    price: float | None = None
    market_cap: float | None = None
    pe: float | None = None
    pb: float | None = None
    roe: float | None = None
    npm: float | None = None
    revenue_growth: float | None = None
    profit_growth: float | None = None


class PeerComparison(APIModel):
    symbol: str
    group: str | None = None            # industry/sector the peers were drawn from
    grouped_by: str | None = None       # "industry" | "sector"
    peers: list[PeerRow] = []
