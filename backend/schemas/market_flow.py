"""Schemas for the FII/DII market-flow endpoints (₹ crore)."""

from datetime import date

from backend.schemas.common import APIModel


class MarketFlowRow(APIModel):
    date: date
    fii_buy: float | None = None
    fii_sell: float | None = None
    fii_net: float | None = None
    dii_buy: float | None = None
    dii_sell: float | None = None
    dii_net: float | None = None


class MarketFlowSummary(APIModel):
    """Latest day + recent history + rolling nets, for the dashboard widget."""
    latest: MarketFlowRow | None = None
    history: list[MarketFlowRow] = []      # chronological (oldest → newest)
    fii_net_window: float | None = None    # sum of fii_net over the window
    dii_net_window: float | None = None
    window_days: int = 0
