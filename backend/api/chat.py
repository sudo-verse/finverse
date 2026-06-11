from fastapi import APIRouter

from backend.schemas.report import ChatOut, ChatRequest
from backend.services.report_service import report_service

router = APIRouter(tags=["genai"])


@router.post("/chat", response_model=ChatOut, summary="RAG document Q&A")
def chat(payload: ChatRequest) -> ChatOut:
    """Answer a question over the ingested documents (ChromaDB + Gemini).
    Optionally scope retrieval to one symbol. Returns the answer plus the
    supporting source excerpts. Requires GEMINI_API_KEY."""
    return report_service.chat(payload)
