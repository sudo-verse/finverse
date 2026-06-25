"""Ownership / shareholding-activity endpoints — promoter, FII and DII QoQ moves."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.ownership import OwnershipActivityRow, OwnershipHistoryRow
from backend.services.ownership_service import ownership_service

router = APIRouter(tags=["ownership"])

_METRIC_RE = "^(promoter|fii|dii|mf|insurance|banks|pension)$"


@router.get("/ownership/activity", response_model=list[OwnershipActivityRow],
            summary="Stocks where a holder class increased or decreased stake (QoQ)")
def ownership_activity(
    db: Session = Depends(get_db),
    metric: str = Query("promoter", pattern=_METRIC_RE,
                        description="holder class: promoter|fii|dii|mf|insurance|banks|pension"),
    direction: str = Query("buying", pattern="^(buying|selling)$",
                           description="buying = biggest increases; selling = decreases"),
    limit: int = Query(50, ge=1, le=200),
    universe: str | None = Query(None, description="all | nifty50 | nifty100 | nifty200 | nifty500"),
) -> list[OwnershipActivityRow]:
    """Market-wide accumulation/reduction for the chosen holder class, from the
    latest two quarterly shareholding snapshots (populated by the shareholding ETL).
    Institutional classes require the `--detail` ETL run; promoter works from the summary run."""
    return ownership_service.activity(db, metric=metric, direction=direction, limit=limit, universe=universe)


@router.get("/ownership/{symbol}/history", response_model=list[OwnershipHistoryRow],
            summary="Quarterly ownership split for one stock (trend)")
def ownership_history(
    symbol: str,
    db: Session = Depends(get_db),
    limit: int = Query(8, ge=2, le=20),
) -> list[OwnershipHistoryRow]:
    """Persisted quarterly shareholding split for a stock, oldest→newest — promoter,
    FII, DII and the DII sub-categories (MF/insurance/banks/pension)."""
    return ownership_service.history(db, symbol, limit=limit)
