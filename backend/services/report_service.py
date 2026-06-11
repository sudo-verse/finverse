"""GenAI endpoints — thin pass-throughs to the existing Gemini integrations:

  - investment report ... app.genai.report_generator.generate_report
                          (context assembly, prompt, DB cache all reused)
  - document Q&A ........ app.genai.rag.answer_question (ChromaDB + Gemini)
"""

import logging
import uuid
from datetime import datetime, timezone

from app.genai import gemini_client
from app.genai.rag import answer_question
from app.genai.report_generator import generate_report
from backend.core.exceptions import NotFoundError, ServiceUnavailableError
from backend.schemas.report import ChatOut, ChatRequest, ChatSource, ReportOut, ReportRequest

logger = logging.getLogger("finverse.api")


def _require_gemini() -> None:
    if not gemini_client.is_configured():
        raise ServiceUnavailableError(
            "GEMINI_API_KEY is not configured — AI reports and document Q&A are disabled."
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

    def chat(self, payload: ChatRequest) -> ChatOut:
        _require_gemini()
        result = answer_question(
            payload.message,
            symbol=payload.symbol.upper() if payload.symbol else None,
            k=payload.k,
        )
        logger.info(
            "chat: answered with %d sources (symbol=%s)",
            len(result["sources"]), payload.symbol,
        )
        return ChatOut(
            id=f"msg-{uuid.uuid4().hex[:12]}",
            content=result["answer"],
            sources=[ChatSource(**s) for s in result["sources"]],
            timestamp=datetime.now(timezone.utc),
        )


report_service = ReportService()
