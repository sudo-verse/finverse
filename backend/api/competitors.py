from fastapi import APIRouter, Path, Query

from backend.schemas.competitor import CompetitorOut
from backend.schemas.nse import NsePeerOut, QuarterOption
from backend.services.competitor_service import competitor_service
from backend.services.nse_service import nse_service

router = APIRouter(tags=["competitors"])


@router.get(
    "/competitors/{symbol}", response_model=CompetitorOut, summary="Peer comparison"
)
def get_competitors(
    symbol: str = Path(min_length=1, max_length=32, description="NSE symbol, e.g. TCS"),
) -> CompetitorOut:
    """Industry peer group with flattened fundamentals/quant metrics per peer,
    plus the target's per-metric value, peer average and rank (1 = best)."""
    return competitor_service.get_competitors(symbol)


@router.get(
    "/competitors/{symbol}/live",
    response_model=list[NsePeerOut],
    summary="Live NSE peer comparison",
)
def get_live_peers(
    symbol: str = Path(min_length=1, max_length=32, description="NSE symbol, e.g. RELIANCE"),
    quarter: str = Query("", description='Optional results quarter, e.g. "2026-03"'),
) -> list[NsePeerOut]:
    """NSE's own industry peer comparison: live price, market cap, P/E, EPS,
    PAT, promoter holding and leverage per peer (cached ~30s)."""
    return nse_service.live_peers(symbol.upper(), quarter=quarter)


@router.get(
    "/competitors/{symbol}/quarters",
    response_model=list[QuarterOption],
    summary="Available results quarters",
)
def get_peer_quarters(
    symbol: str = Path(min_length=1, max_length=32, description="NSE symbol"),
) -> list[QuarterOption]:
    """Quarters available for the live peer comparison's results data."""
    return nse_service.peer_quarters(symbol.upper())
