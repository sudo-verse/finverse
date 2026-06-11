from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.database import get_db
from backend.schemas.common import Paginated
from backend.schemas.signal import SignalFacets, SignalOut
from backend.services.signal_service import signal_service

router = APIRouter(tags=["signals"])


@router.get("/signals", response_model=Paginated[SignalOut], summary="Signal feed")
def list_signals(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size, alias="pageSize"),
    signal: str | None = Query(None, description="BUY | SELL | HOLD"),
    sentiment: str | None = Query(None, description="positive | negative | neutral"),
    source: str | None = Query(None, description="Exact source name"),
    search: str | None = Query(None, description="Matches symbol, company name or headline"),
) -> Paginated[SignalOut]:
    """Paginated, filterable feed of engine-generated Buy/Sell/Hold signals."""
    return signal_service.list_signals(
        db,
        page=page,
        page_size=page_size,
        signal=signal,
        sentiment=sentiment,
        source=source,
        search=search,
    )


@router.get("/signals/facets", response_model=SignalFacets, summary="Filter options")
def signal_facets(db: Session = Depends(get_db)) -> SignalFacets:
    """Distinct signal types, sources and sentiments present in the data —
    drives the filter dropdowns so the UI never hardcodes them."""
    return signal_service.facets(db)
