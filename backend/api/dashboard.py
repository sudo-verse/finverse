from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.dashboard import DashboardOut
from backend.services.dashboard_service import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut, summary="Dashboard aggregates")
def get_dashboard(db: Session = Depends(get_db)) -> DashboardOut:
    """Headline metrics, signal/industry distributions, 14-day signal trend
    and the latest signals & news events."""
    return dashboard_service.get_dashboard(db)
