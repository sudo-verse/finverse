"""Ownership / shareholding-activity endpoints (promoter accumulation; FII/DII next)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.ownership import PromoterActivityRow
from backend.services.ownership_service import ownership_service

router = APIRouter(tags=["ownership"])


@router.get("/ownership/promoter-activity", response_model=list[PromoterActivityRow],
            summary="Stocks where promoters increased/decreased stake (QoQ)")
def promoter_activity(
    db: Session = Depends(get_db),
    direction: str = Query("buying", pattern="^(buying|selling)$",
                           description="buying = biggest stake increases; selling = decreases"),
    limit: int = Query(50, ge=1, le=200),
) -> list[PromoterActivityRow]:
    """Market-wide promoter accumulation/reduction, from the latest two quarterly
    shareholding snapshots (populated by the shareholding ETL)."""
    return ownership_service.promoter_activity(db, direction=direction, limit=limit)
