"""AI Research Copilot endpoints (/api/research/*).

Chat and compare stream by default as Server-Sent Events so the UI can render
tokens as they arrive:

    event: sources   data: [SourceCitation...]      (sent once, pre-answer)
    event: delta     data: {"text": "..."}          (repeated)
    event: done      data: ResearchChatOut          (full envelope, persisted)
    event: error     data: {"detail": "..."}

Set `"stream": false` in the body to get a plain JSON ResearchChatOut instead.
"""

import json
import logging

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.models import User
from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.schemas.research import (
    CompanySourcesOut,
    ResearchChatOut,
    ResearchChatRequest,
    ResearchCompanyOut,
    ResearchCompareRequest,
    ResearchHistoryItem,
)
from backend.services.research_service import research_service

logger = logging.getLogger("finverse.api")

router = APIRouter(prefix="/research", tags=["research"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # disable proxy buffering (nginx et al.)
}


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def _respond(citations, token_gen, meta, stream: bool):
    """Shared chat/compare response path: SSE stream or buffered JSON."""
    if not stream:
        answer = "".join(token_gen)
        return research_service.finalize(meta, citations, answer)

    def event_stream():
        yield _sse("sources", [c.model_dump(by_alias=True) for c in citations])
        parts: list[str] = []
        try:
            for token in token_gen:
                parts.append(token)
                yield _sse("delta", {"text": token})
        except Exception:
            logger.exception("research: generation failed mid-stream")
            yield _sse("error", {"detail": "Generation failed. Please retry."})
            return
        out = research_service.finalize(meta, citations, "".join(parts))
        yield _sse("done", out.model_dump(by_alias=True))

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers=SSE_HEADERS)


@router.post("/chat", summary="Company-aware research chat",
             response_model=ResearchChatOut)
def research_chat(payload: ResearchChatRequest, user: User = Depends(get_current_user)):
    """Ask a plain-English question about one company. Answers are grounded in
    the indexed filings (hybrid RAG) plus Finverse structured data, with
    numbered source citations. Streams SSE unless `stream` is false."""
    citations, token_gen, meta = research_service.prepare_chat(user.id, payload)
    return _respond(citations, token_gen, meta, payload.stream)


@router.post("/compare", summary="Compare two or three companies",
             response_model=ResearchChatOut)
def research_compare(payload: ResearchCompareRequest, user: User = Depends(get_current_user)):
    """Comparison mode: retrieves documents for each company and generates a
    head-to-head analyst report."""
    citations, token_gen, meta = research_service.prepare_compare(user.id, payload)
    return _respond(citations, token_gen, meta, payload.stream)


@router.get("/companies", response_model=list[ResearchCompanyOut],
            summary="Researchable companies")
def research_companies(
    db: Session = Depends(get_db),
    search: str | None = Query(None, description="Filter by symbol or name"),
    limit: int = Query(50, ge=1, le=500),
) -> list[ResearchCompanyOut]:
    """Company master annotated with how many document chunks are indexed."""
    return research_service.list_companies(db, search=search, limit=limit)


@router.get("/sources/{symbol}", response_model=CompanySourcesOut,
            summary="Available sources for a company")
def research_sources(
    db: Session = Depends(get_db),
    symbol: str = Path(min_length=1, max_length=32),
) -> CompanySourcesOut:
    """What the copilot can see for this company: indexed documents grouped by
    type/year plus structured-data availability (financials, prices, news)."""
    return research_service.company_sources(db, symbol)


@router.get("/history", response_model=list[ResearchHistoryItem],
            summary="Past research Q&A")
def research_history(
    user: User = Depends(get_current_user),
    symbol: str | None = Query(None, description="Filter to one company"),
    limit: int = Query(30, ge=1, le=200),
) -> list[ResearchHistoryItem]:
    return research_service.history(user.id, symbol, limit)
