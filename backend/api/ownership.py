"""Ownership / shareholding-activity endpoints — promoter, FII and DII QoQ moves."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.ownership import OwnershipActivityRow
from backend.services.ownership_service import ownership_service

router = APIRouter(tags=["ownership"])


@router.get("/ownership/activity", response_model=list[OwnershipActivityRow],
            summary="Stocks where promoter/FII/DII increased or decreased stake (QoQ)")
def ownership_activity(
    db: Session = Depends(get_db),
    metric: str = Query("promoter", pattern="^(promoter|fii|dii)$",
                        description="which holder class to rank by"),
    direction: str = Query("buying", pattern="^(buying|selling)$",
                           description="buying = biggest increases; selling = decreases"),
    limit: int = Query(50, ge=1, le=200),
) -> list[OwnershipActivityRow]:
    """Market-wide accumulation/reduction for the chosen holder class, from the
    latest two quarterly shareholding snapshots (populated by the shareholding ETL).
    FII/DII require the `--detail` ETL run; promoter works from the summary run."""
    return ownership_service.activity(db, metric=metric, direction=direction, limit=limit)
