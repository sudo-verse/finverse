"""Account usage endpoint (/api/usage) — today's metered usage vs plan limits."""

from fastapi import APIRouter, Depends

from app.db.models import User
from backend.core.deps import get_current_user
from backend.schemas.usage import UsageOut
from backend.services.usage_service import usage_service

router = APIRouter(tags=["account"])


@router.get("/usage", response_model=UsageOut, summary="Today's plan usage")
def get_usage(user: User = Depends(get_current_user)) -> UsageOut:
    return UsageOut.model_validate(usage_service.usage(user.id, user.plan))
