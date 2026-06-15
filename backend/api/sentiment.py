"""AI Sentiment Intelligence endpoints (/api/sentiment/*).

The composite endpoint returns everything the dashboard needs in one call;
the per-pillar endpoints exist for lighter-weight consumers.
"""

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.sentiment import (
    LeaderboardEntry,
    PillarDetail,
    SentimentHistoryPoint,
    SentimentOut,
)
from backend.services.sentiment_service import sentiment_service

router = APIRouter(prefix="/sentiment", tags=["sentiment"])

SymbolPath = Path(min_length=1, max_length=32)


# NOTE: declared before /{symbol} so "leaderboard" isn't matched as a symbol.
@router.get("/leaderboard", response_model=list[LeaderboardEntry],
            summary="Top/bottom NSE stocks by sentiment score")
def leaderboard(
    db: Session = Depends(get_db),
    limit: int = Query(5, ge=1, le=50),
    order: str = Query("top", pattern="^(top|bottom)$"),
    min_confidence: float = Query(0.0, ge=0, le=1,
                                  description="Drop low-coverage scores (0-1)"),
) -> list[LeaderboardEntry]:
    """Rank companies by their latest daily sentiment snapshot. `order=bottom`
    surfaces the weakest names. Coverage is whatever has been scored (the daily
    ETL refreshes the whole universe)."""
    return sentiment_service.leaderboard(db, limit=limit, order=order,
                                         min_confidence=min_confidence)


def _pillar(db: Session, symbol: str, name: str) -> PillarDetail:
    out = sentiment_service.compute(db, symbol)
    return next(p for p in out.pillars if p.name.lower() == name)


@router.get("/{symbol}", response_model=SentimentOut,
            summary="Composite explainable sentiment (0-100)")
def overall(db: Session = Depends(get_db), symbol: str = SymbolPath) -> SentimentOut:
    """Weighted score — Technical 30%, Fundamental 30%, News 20%, Ownership
    10%, Market 10% (weights renormalize over pillars with data). Includes
    factor-level explanations, reasons/risks, momentum ranges, pivots,
    MA levels, news split and shareholding deltas. Cached ~10 min and
    snapshotted daily for the history chart."""
    return sentiment_service.compute(db, symbol)


@router.get("/technical/{symbol}", response_model=PillarDetail, summary="Technical pillar")
def technical(db: Session = Depends(get_db), symbol: str = SymbolPath) -> PillarDetail:
    return _pillar(db, symbol, "technical")


@router.get("/fundamental/{symbol}", response_model=PillarDetail, summary="Fundamental pillar")
def fundamental(db: Session = Depends(get_db), symbol: str = SymbolPath) -> PillarDetail:
    return _pillar(db, symbol, "fundamental")


@router.get("/news/{symbol}", response_model=PillarDetail, summary="News pillar")
def news(db: Session = Depends(get_db), symbol: str = SymbolPath) -> PillarDetail:
    return _pillar(db, symbol, "news")


@router.get("/ownership/{symbol}", response_model=PillarDetail, summary="Ownership pillar")
def ownership(db: Session = Depends(get_db), symbol: str = SymbolPath) -> PillarDetail:
    return _pillar(db, symbol, "ownership")


@router.get("/history/{symbol}", response_model=list[SentimentHistoryPoint],
            summary="Daily sentiment snapshots")
def history(
    symbol: str = SymbolPath,
    limit: int = Query(90, ge=1, le=365),
) -> list[SentimentHistoryPoint]:
    return sentiment_service.history(symbol, limit)


@router.post("/recompute/{symbol}", response_model=SentimentOut,
             summary="Force a fresh computation")
def recompute(db: Session = Depends(get_db), symbol: str = SymbolPath) -> SentimentOut:
    return sentiment_service.compute(db, symbol, force=True)
