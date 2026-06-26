"""Stock screener endpoints (/api/screener, /api/screens)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models import User
from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.schemas.saved_screen import SavedScreenCreate, SavedScreenOut
from backend.schemas.screener import ScreenerRow
from backend.services import screener_service, universe_service
from backend.services.saved_screen_service import saved_screen_service

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


@router.get("/screens", response_model=list[SavedScreenOut], summary="Saved screens")
def list_screens(db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)) -> list[SavedScreenOut]:
    """The user's saved screener filter sets (newest first)."""
    return saved_screen_service.list(db, user.id)


@router.post("/screens", response_model=SavedScreenOut, status_code=201, summary="Save a screen")
def save_screen(payload: SavedScreenCreate, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)) -> SavedScreenOut:
    """Persist a named filter set. Saving over an existing name updates it. Set
    notify=true to be alerted when a new stock enters the screen."""
    return saved_screen_service.create(db, user.id, payload)


@router.delete("/screens/{screen_id}", summary="Delete a saved screen")
def delete_screen(screen_id: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)) -> dict:
    saved_screen_service.delete(db, user.id, screen_id)
    return {"status": "deleted"}
