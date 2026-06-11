from typing import Any

from fastapi import APIRouter, Query

from backend.schemas.nse import (
    IndexQuote,
    IntradaySeries,
    MarketMovers,
    MarketOverview,
    MarqueeItem,
    TurnoverRow,
)
from backend.services.nse_service import nse_service

router = APIRouter(tags=["market"])


@router.get("/market/overview", response_model=MarketOverview, summary="Live market overview")
def market_overview() -> MarketOverview:
    """Live index quotes, GIFT Nifty futures, USD/INR, total market cap and
    the exchange's market-status code (cached ~30s)."""
    return nse_service.market_overview()


@router.get("/market/movers", response_model=MarketMovers, summary="Top gainers & losers")
def market_movers() -> MarketMovers:
    """NSE's top-ten gainers and losers with live prices."""
    return nse_service.movers()


@router.get("/market/block-deals", summary="Block deal sessions")
def block_deals() -> Any:
    """Raw block-deal session windows (frequently empty outside session hours)."""
    return nse_service.block_deals()


@router.get("/market/indices", response_model=list[IndexQuote], summary="All NSE indices")
def all_indices() -> list[IndexQuote]:
    """Live quotes for every NSE index (broad, sectoral, thematic, strategy)."""
    return nse_service.all_indices()


@router.get("/market/index-chart", response_model=IntradaySeries, summary="Index intraday chart")
def index_chart(
    index: str = Query("NIFTY 50", description='Index name, e.g. "NIFTY 50"'),
    flag: str = Query("1D", description='Chart window, e.g. "1D"'),
) -> IntradaySeries:
    """Intraday tick series for an index (NSE getGraphChart)."""
    return nse_service.index_chart(index, flag=flag)


@router.get("/market/marquee", response_model=list[MarqueeItem], summary="Ticker marquee")
def marquee() -> list[MarqueeItem]:
    """NIFTY 50 constituents with live price and % change — for ticker strips."""
    return nse_service.marquee()


@router.get("/market/turnover", response_model=list[TurnoverRow], summary="Market turnover")
def turnover() -> list[TurnoverRow]:
    """Segment-wise equity market turnover, trades and volume vs previous day."""
    return nse_service.turnover()
