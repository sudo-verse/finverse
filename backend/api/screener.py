"""Stock screener endpoint (/api/screener)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.screener import ScreenerRow
from backend.services import screener_service, universe_service

router = APIRouter(tags=["screener"])


@router.get("/screener", response_model=list[ScreenerRow],
            summary="Screening universe (all companies, computed metrics)")
def screener(
    db: Session = Depends(get_db),
    universe: str | None = Query(None, description="all | nifty50 | nifty100 | nifty200 | nifty500"),
) -> list[ScreenerRow]:
    """One row per company: valuation (PE/PB/M.Cap), profitability (ROE/ROCE/
    NPM), leverage, YoY growth and the latest sentiment snapshot. Optionally
    narrowed to an NSE index. Cached server-side for 10 minutes; filter and sort
    on the client."""
    return universe_service.filter_rows(screener_service.screen(db), universe)
