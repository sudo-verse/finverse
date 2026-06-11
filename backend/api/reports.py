from fastapi import APIRouter

from backend.schemas.report import ReportOut, ReportRequest
from backend.services.report_service import report_service

router = APIRouter(tags=["genai"])


@router.post("/report", response_model=ReportOut, summary="AI investment report")
def generate_report(payload: ReportRequest) -> ReportOut:
    """Generate (or return the cached) Gemini investment report for a symbol.
    Set `useCache: false` to force regeneration. Requires GEMINI_API_KEY."""
    return report_service.generate(payload)
