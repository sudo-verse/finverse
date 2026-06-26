"""Schema for the DCF / scenario intrinsic-value builder."""

from backend.schemas.common import APIModel


class DcfScenario(APIModel):
    name: str                       # bull | base | bear
    growth: float                   # annual FCF growth (fraction)
    terminal_growth: float
    discount: float                 # cost of equity / discount rate
    years: int
    intrinsic_value: float | None = None    # per share
    upside_pct: float | None = None


class DcfOut(APIModel):
    symbol: str
    name: str | None = None
    price: float | None = None
    base_fcf: float | None = None           # latest annual FCF proxy (₹)
    fcf_source: str | None = None           # operating cash flow | net income
    shares: float | None = None
    historical_growth: float | None = None
    applicable: bool = True
    note: str | None = None
    scenarios: list[DcfScenario] = []
