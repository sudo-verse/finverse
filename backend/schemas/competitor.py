from backend.schemas.common import APIModel


class PeerRow(APIModel):
    """Flattened L5 + L4 metrics for one peer (competitor_analysis.metrics_for)."""

    symbol: str
    company: str | None = None
    revenue_growth: float | None = None
    earnings_growth: float | None = None
    net_profit_margin: float | None = None
    roe: float | None = None
    roce: float | None = None
    debt_to_equity: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    cumulative_return: float | None = None
    annualized_volatility: float | None = None
    sharpe_ratio: float | None = None


class MetricComparison(APIModel):
    """Target value vs peer group for one metric (1 = best)."""

    metric: str
    value: float | None = None
    peer_avg: float | None = None
    rank: int | None = None
    out_of: int


class CompetitorOut(APIModel):
    symbol: str
    company: str | None = None
    industry: str
    peer_count: int
    overall_rank: int | None = None  # average of per-metric ranks, rounded
    peers: list[PeerRow]
    comparison: list[MetricComparison]
