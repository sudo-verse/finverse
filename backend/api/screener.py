"""Stock screener endpoint (/api/screener)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.screener import ScreenerRow
from backend.services import screener_service

router = APIRouter(tags=["screener"])


@router.get("/screener", response_model=list[ScreenerRow],
            summary="Screening universe (all companies, computed metrics)")
def screener(db: Session = Depends(get_db)) -> list[ScreenerRow]:
    """One row per company: valuation (PE/PB/M.Cap), profitability (ROE/ROCE/
    NPM), leverage, YoY growth and the latest sentiment snapshot. Cached
    server-side for 10 minutes; filter and sort on the client."""
    return screener_service.screen(db)
