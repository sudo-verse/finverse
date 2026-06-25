from typing import Any

from fastapi import APIRouter, Query, Request

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.market_flow import MarketFlowSummary
from backend.schemas.nse import (
    IndexQuote,
    IntradaySeries,
    MarketMovers,
    MarketOverview,
    MarqueeItem,
    TurnoverRow,
)
from backend.services.market_flow_service import market_flow_service
from backend.services.nse_service import nse_service

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

