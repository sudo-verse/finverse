from fastapi import APIRouter, Depends

from app.db.models import User
from backend.core.deps import get_current_user
from backend.schemas.report import ReportOut, ReportRequest
from backend.services.report_service import report_service
from backend.services.usage_service import usage_service

router = APIRouter(tags=["genai"])


@router.post("/report", response_model=ReportOut, summary="AI investment report")
def generate_report(payload: ReportRequest, user: User = Depends(get_current_user)) -> ReportOut:
    """Generate (or return the cached) Gemini investment report for a symbol.
    Set `useCache: false` to force regeneration. Only a freshly generated report
    counts against the daily AI-report quota — cached hits are free. Requires
    GEMINI_API_KEY."""
    usage_service.check(user.id, user.plan, "report")
    result = report_service.generate(payload)
    if not result.cached:
        usage_service.record(user.id, "report")
    return result
