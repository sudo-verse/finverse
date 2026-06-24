"""GenAI endpoints — thin pass-throughs to the existing Gemini integrations:

  - investment report ... app.genai.report_generator.generate_report
                          (context assembly, prompt, DB cache all reused)
"""

import logging

from app.genai import gemini_client
from app.genai.report_generator import generate_report
from backend.core.exceptions import NotFoundError, ServiceUnavailableError
from backend.schemas.report import ReportOut, ReportRequest

logger = logging.getLogger("finverse.api")


def _require_gemini() -> None:
    if not gemini_client.is_configured():
        raise ServiceUnavailableError(
            "GEMINI_API_KEY is not configured — AI reports are disabled."
        )


class ReportService:
    def generate(self, payload: ReportRequest) -> ReportOut:
        _require_gemini()
        symbol = payload.symbol.upper()
        try:
            result = generate_report(symbol, use_cache=payload.use_cache)
        except gemini_client.GeminiNotConfigured as exc:  # belt & braces
            raise ServiceUnavailableError(str(exc)) from exc

        if not result.get("report_md"):
            raise NotFoundError(f"Could not generate a report for {symbol}.")
        logger.info(
            "report: %s (cached=%s, model=%s)", symbol, result["cached"], result["model"]
        )
        return ReportOut(**result)


report_service = ReportService()
