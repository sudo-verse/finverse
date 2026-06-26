from datetime import date

from pydantic import Field

from backend.schemas.common import APIModel


class HoldingOut(APIModel):
    symbol: str
    industry: str | None = None
    quantity: float
    avg_price: float | None = None
    price: float | None = None  # latest close
    value: float | None = None
    cost: float | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    weight: float | None = None
    day_change_pct: float | None = None


class SectorAllocation(APIModel):
    sector: str
    weight: float  # 0–1
    value: float | None = None


class PortfolioSummary(APIModel):
    total_value: float
    total_cost: float | None = None
    total_pnl: float | None = None
    total_pnl_pct: float | None = None
    day_pnl: float | None = None
    day_pnl_pct: float | None = None
    num_holdings: int
    num_sectors: int
    hhi: float | None = None
    effective_holdings: float | None = None
    top_concentration: float | None = None
    annualized_volatility: float | None = None
    annualized_return: float | None = None
    sharpe_ratio: float | None = None


class MarketCapAllocation(APIModel):
    bucket: str            # Large cap | Mid cap | Small cap | Unknown
    weight: float          # 0–1
    value: float | None = None


class GrowthPoint(APIModel):
    date: date
    value: float
    invested: float | None = None


class PortfolioOut(APIModel):
    summary: PortfolioSummary
    holdings: list[HoldingOut]
    sector_allocation: list[SectorAllocation]
    market_cap_allocation: list[MarketCapAllocation] = []
    growth: list[GrowthPoint]


class HoldingCreate(APIModel):
    symbol: str = Field(min_length=1, max_length=32)
    quantity: float = Field(gt=0)
    avg_price: float | None = Field(default=None, gt=0)
