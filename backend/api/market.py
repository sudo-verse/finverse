from typing import Any

from fastapi import APIRouter, Query, Request

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.deals import DealRow
from backend.schemas.earnings import EarningsRow
from backend.schemas.events import CorporateEventRow
from backend.schemas.market_flow import MarketFlowSummary
from backend.schemas.radar import RadarRow
from backend.schemas.sectors import SectorPerf
from backend.schemas.nse import (
    IndexQuote,
    IntradaySeries,
    MarketMovers,
    MarketOverview,
    MarqueeItem,
    TurnoverRow,
)
from backend.services import earnings_service
from backend.services.deals_service import deals_service
from backend.services.events_service import events_service
from backend.services.market_flow_service import market_flow_service
from backend.services.nse_service import nse_service
from backend.services.radar_service import radar_service
from backend.services.sector_service import sector_service

router = APIRouter(tags=["market"])


@router.get("/market/flows", response_model=MarketFlowSummary,
            summary="Daily FII/DII cash-market flows (₹ crore)")
def market_flows(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=250, description="trading days of history"),
) -> MarketFlowSummary:
    """Latest provisional FII/DII buy/sell/net plus the rolling history and
    window net totals. Populated daily post-close by the market-flow ETL."""
    return market_flow_service.summary(db, days=days)


@router.get("/market/deals", response_model=list[DealRow],
            summary="Bulk & block deals (largest first)")
def market_deals(
    db: Session = Depends(get_db),
    type: str | None = Query(None, pattern="^(bulk|block)$", description="deal type filter"),
    side: str | None = Query(None, pattern="^(BUY|SELL)$", description="buy/sell filter"),
    symbol: str | None = Query(None, description="restrict to one stock"),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
) -> list[DealRow]:
    """Disclosed large trades by named clients, biggest by value first.
    Populated daily post-close by the deals ETL (NSE large-deal snapshot)."""
    return deals_service.recent(db, deal_type=type, side=side, symbol=symbol, days=days, limit=limit)


@router.get("/market/events", response_model=list[CorporateEventRow],
            summary="Corporate events calendar (results, dividends, splits…)")
def market_events(
    db: Session = Depends(get_db),
    window: str = Query("upcoming", pattern="^(upcoming|recent|all)$"),
    type: str | None = Query(None, description="event type, e.g. result|dividend|split"),
    symbol: str | None = Query(None, description="restrict to one stock"),
    days: int = Query(30, ge=1, le=180),
    limit: int = Query(200, ge=1, le=500),
) -> list[CorporateEventRow]:
    """Upcoming/recent corporate events from NSE's board-meeting calendar +
    corporate actions. Populated daily by the events ETL."""
    return events_service.list(db, window=window, event_type=type, symbol=symbol, days=days, limit=limit)


@router.get("/market/overview", response_model=MarketOverview, summary="Live market overview")
def market_overview() -> MarketOverview:
    """Live index quotes, GIFT Nifty futures, USD/INR, total market cap and
    the exchange's market-status code (cached ~30s)."""
    return nse_service.market_overview()


@router.get("/market/sectors", response_model=list[SectorPerf],
            summary="Sector index performance (day/week/month/year)")
def market_sectors() -> list[SectorPerf]:
    """NSE sectoral indices with day/week/month/year % change — for the
    sector-rotation heatmap. Live (cached ~60s)."""
    return sector_service.heatmap()


@router.get("/market/radar", response_model=list[RadarRow],
            summary="Stocks near their 52-week high or low")
def market_radar(
    db: Session = Depends(get_db),
    band: str = Query("high", pattern="^(high|low)$"),
    threshold: float = Query(3.0, ge=0.1, le=25, description="% within the extreme"),
    limit: int = Query(100, ge=1, le=500),
) -> list[RadarRow]:
    """Momentum/breakout radar: stocks within `threshold`% of their 52-week
    high or low, closest to the extreme first (computed from price history)."""
    return radar_service.screen(db, band=band, threshold=threshold, limit=limit)


@router.get("/market/earnings", response_model=list[EarningsRow],
            summary="Earnings-growth (momentum) tracker")
def market_earnings(
    db: Session = Depends(get_db),
    sort: str = Query("pat", pattern="^(pat|revenue|margin)$"),
    limit: int = Query(50, ge=1, le=300),
) -> list[EarningsRow]:
    """Latest-FY YoY growth ranked by PAT growth, revenue growth or net-margin
    expansion. `momentum` flags whether PAT growth is accelerating or
    decelerating versus the prior year (annual financials, cached ~10m)."""
    return earnings_service.tracker(db, sort=sort, limit=limit)


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


@router.get("/nse/announcements", summary="Proxy corporate announcements")
def nse_announcements() -> list:
    """Fetch corporate announcements directly from the local (working) scraper."""
    from app.ingestion.nse_fetcher import fetch_nse_announcements
    return fetch_nse_announcements()


@router.get("/nse/equity-stockIndices", summary="Proxy equity stock indices")
def nse_equity_stock_indices() -> dict:
    """Fetch equity stock indices (NIFTY 500) using the working client."""
    client = nse_service._get_client()
    data = client.get_data()
    return {"data": data}


@router.get("/nse/quote", summary="Proxy quote api")
def nse_quote(functionName: str, request: Request) -> Any:
    """Proxy Quote API (NextApi GetQuoteApi)."""
    client = nse_service._get_client()
    params = dict(request.query_params)
    params.pop("functionName", None)
    return client.quote_api(functionName, **params)


@router.get("/nse/next", summary="Proxy next api")
def nse_next(functionName: str, request: Request) -> Any:
    """Proxy Next API (NextApi apiClient)."""
    client = nse_service._get_client()
    params = dict(request.query_params)
    params.pop("functionName", None)
    return client.next_api(functionName, **params)


@router.get("/nse/home", summary="Proxy home api")
def nse_home(functionName: str, request: Request) -> Any:
    """Proxy Home API (NextApi homeApi)."""
    client = nse_service._get_client()
    params = dict(request.query_params)
    params.pop("functionName", None)
    return client.home_api(functionName, **params)

