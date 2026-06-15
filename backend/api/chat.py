from fastapi import APIRouter, Depends

from app.db.models import User
from backend.core.deps import get_current_user
from backend.schemas.report import ChatOut, ChatRequest
from backend.services.report_service import report_service
from backend.services.usage_service import usage_service

router = APIRouter(tags=["genai"])


@router.post("/chat", response_model=ChatOut, summary="RAG document Q&A")
def chat(payload: ChatRequest, user: User = Depends(get_current_user)) -> ChatOut:
    """Answer a question over the ingested documents (ChromaDB + Gemini).
    Optionally scope retrieval to one symbol. Counts against the daily AI-chat
    quota for the user's plan. Requires GEMINI_API_KEY."""
    usage_service.enforce(user.id, user.plan, "chat")
    return report_service.chat(payload)
