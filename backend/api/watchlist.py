"""Watchlist + alerts endpoints (/api/watchlist, /api/alerts)."""

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.watchlist import (
    AlertEventOut,
    AlertRuleCreate,
    AlertRuleOut,
    WatchlistCreate,
    WatchlistItemOut,
)
from backend.services.watchlist_service import watchlist_service

router = APIRouter(tags=["watchlist"])


@router.get("/watchlist", response_model=list[WatchlistItemOut], summary="Tracked stocks")
def list_watchlist(db: Session = Depends(get_db)) -> list[WatchlistItemOut]:
    """Watchlist enriched with live price, latest sentiment snapshot and
    active alert count (enrichment is best-effort)."""
    return watchlist_service.list(db)


@router.post("/watchlist", status_code=201, summary="Track a stock")
def add_to_watchlist(payload: WatchlistCreate, db: Session = Depends(get_db)) -> dict:
    watchlist_service.add(db, payload)
    return {"status": "added"}


@router.delete("/watchlist/{symbol}", summary="Untrack a stock (and its alerts)")
def remove_from_watchlist(db: Session = Depends(get_db), symbol: str = Path(max_length=32)) -> dict:
    watchlist_service.remove(db, symbol)
    return {"status": "removed"}


@router.get("/alerts", response_model=list[AlertRuleOut], summary="Alert rules")
def list_alerts(db: Session = Depends(get_db), symbol: str | None = Query(None)) -> list[AlertRuleOut]:
    return watchlist_service.list_rules(db, symbol)


@router.post("/alerts", response_model=AlertRuleOut, status_code=201, summary="Create alert rule")
def create_alert(payload: AlertRuleCreate, db: Session = Depends(get_db)) -> AlertRuleOut:
    """Kinds: price_above/below (threshold = ₹ level), sentiment_above/below
    (threshold = 0-100 score), promoter_change (threshold = pp, default 0.5),
    buy_signal (no threshold). Evaluated every few minutes; 24h cooldown."""
    return watchlist_service.create_rule(db, payload)


@router.delete("/alerts/{rule_id}", summary="Delete alert rule")
def delete_alert(rule_id: int, db: Session = Depends(get_db)) -> dict:
    watchlist_service.delete_rule(db, rule_id)
    return {"status": "deleted"}


@router.get("/alerts/events", response_model=list[AlertEventOut], summary="Fired alerts")
def list_events(db: Session = Depends(get_db), limit: int = Query(30, ge=1, le=200)) -> list[AlertEventOut]:
    return watchlist_service.list_events(db, limit)


@router.post("/alerts/events/seen", summary="Mark all fired alerts as read")
def mark_seen(db: Session = Depends(get_db)) -> dict:
    watchlist_service.mark_events_seen(db)
    return {"status": "ok"}
