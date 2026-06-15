from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import User
from backend.core.database import get_db
from backend.core.deps import get_current_user_optional
from backend.schemas.dashboard import DashboardOut
from backend.services.dashboard_service import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut, summary="Dashboard aggregates")
def get_dashboard(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> DashboardOut:
    """Headline metrics, signal/industry distributions, 14-day signal trend and
    the latest signals & news events. The portfolio card is populated only when
    a valid token is supplied (per-user)."""
    return dashboard_service.get_dashboard(db, user_id=user.id if user else None)
