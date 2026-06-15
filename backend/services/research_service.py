"""AI Research Copilot service — orchestrates the app.genai.research pipeline.

Reuses existing Finverse modules rather than re-implementing them:
  - retrieval/generation .... app.genai.research (hybrid RAG + Gemini)
  - structured context ...... app.genai.report_generator.build_context
                              (quant metrics, fundamentals, peers, signals)
  - persistence ............. app.db.repository research-chat helpers
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Company, FinancialStatement, NewsSignal, PriceHistory
from app.db.repository import get_research_history, save_research_chat
from app.genai import gemini_client, research
from app.genai.report_generator import build_context
from backend.core.exceptions import NotFoundError, ServiceUnavailableError
from backend.schemas.research import (
    CompanySourcesOut,
    DocTypeSummary,
    ResearchChatOut,
    ResearchChatRequest,
    ResearchCompanyOut,
    ResearchCompareRequest,
    ResearchHistoryItem,
    SourceCitation,
)

logger = logging.getLogger("finverse.api")

# Question pool used to suggest follow-ups the user hasn't asked yet.
FOLLOW_UP_POOL = [
    "What are the key risks?",
    "What are the main growth drivers?",
    "How is the management commentary trending?",
    "Did promoter holding change recently?",
    "What changed in the latest quarterly results?",
    "How does it compare with its closest competitor?",
    "What is the long-term investment thesis?",
    "Explain this company like I'm a beginner.",
]


def _require_gemini() -> None:
    if not gemini_client.is_configured():
        raise ServiceUnavailableError(
            "GEMINI_API_KEY is not configured — the AI Research Copilot is disabled."
        )


def _citation(src: dict) -> SourceCitation:
    return SourceCitation(
        id=src["id"],
        label=research.citation_label(src),
        source=src["source"],
        doc_type=src.get("doc_type"),
        year=src.get("year"),
        page=src.get("page"),
        symbol=src.get("symbol"),
        snippet=(src.get("text") or "")[:280],
    )


def _follow_ups(question: str, history: list) -> list[str]:
    """Suggest questions not yet covered in this conversation."""
    asked = question.lower() + " ".join(
        t.content.lower() for t in history if t.role == "user"
    )
    out = []
    for q in FOLLOW_UP_POOL:
        anchor = q.lower().rstrip("?").split()[-1]  # cheap topical overlap check
        if anchor not in asked:
            out.append(q)
        if len(out) == 3:
            break
    return out


def _structured_context(symbol: str) -> dict | None:
    """Finverse's structured view of the company; never fail the chat over it."""
    try:
        return build_context(symbol)
    except Exception as e:
        logger.warning("research: structured context failed for %s: %s", symbol, e)
        return None


class ResearchService:
    # ------------------------------------------------------------------ chat
    def prepare_chat(self, user_id: int, payload: ResearchChatRequest):
        """Run retrieval + start generation. Returns (sources, token_gen, meta).

        Split from response assembly so the API layer can stream tokens while
        we accumulate the full answer for persistence.
        """
        _require_gemini()
        symbol = payload.symbol.upper()
        history = [t.model_dump() for t in payload.history]
        sources, token_gen = research.research_answer(
            payload.message,
            symbol=symbol,
            history=history,
            structured=_structured_context(symbol),
            doc_type=payload.doc_type,
            year=payload.year,
        )
        citations = [_citation(s) for s in sources]
        follow_ups = _follow_ups(payload.message, payload.history)
        return citations, token_gen, {"user_id": user_id, "symbol": symbol, "mode": "chat",
                                      "question": payload.message,
                                      "follow_ups": follow_ups}

    def prepare_compare(self, user_id: int, payload: ResearchCompareRequest):
        _require_gemini()
        symbols = [s.upper() for s in payload.symbols]
        structured = {sym: _structured_context(sym) for sym in symbols}
        sources, token_gen = research.research_compare(
            symbols, question=payload.message, structured=structured
        )
        citations = [_citation(s) for s in sources]
        label = " vs ".join(symbols)
        question = payload.message or f"Compare {label}"
        return citations, token_gen, {"user_id": user_id, "symbol": label, "mode": "compare",
                                      "question": question,
                                      "follow_ups": _follow_ups(question, [])}

    def finalize(self, meta: dict, citations: list[SourceCitation],
                 answer: str) -> ResearchChatOut:
        """Persist the exchange and shape the response envelope."""
        save_research_chat(
            user_id=meta["user_id"],
            symbol=meta["symbol"],
            question=meta["question"],
            answer=answer,
            sources_json=json.dumps([c.model_dump() for c in citations]),
            mode=meta["mode"],
        )
        return ResearchChatOut(
            id=f"res-{uuid.uuid4().hex[:12]}",
            content=answer,
            sources=citations,
            follow_ups=meta["follow_ups"],
            timestamp=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------- companies/sources
    def list_companies(self, session: Session, search: str | None = None,
                       limit: int = 50) -> list[ResearchCompanyOut]:
        indexed = research.symbols_with_documents()
        q = session.query(Company).order_by(Company.symbol)
        if search:
            like = f"%{search}%"
            q = q.filter((Company.symbol.ilike(like)) | (Company.name.ilike(like)))
        return [
            ResearchCompanyOut(
                symbol=c.symbol,
                name=c.name,
                industry=c.industry,
                indexed_chunks=indexed.get(c.symbol, 0),
            )
            for c in q.limit(limit).all()
        ]

    def company_sources(self, session: Session, symbol: str) -> CompanySourcesOut:
        symbol = symbol.upper()
        company = session.query(Company).filter_by(symbol=symbol).first()
        if not company:
            raise NotFoundError(f"Unknown symbol: {symbol}")

        summary = research.source_summary(symbol)
        has_fin = (
            session.query(FinancialStatement.id)
            .filter_by(company_id=company.id).first() is not None
        )
        has_prices = (
            session.query(PriceHistory.id)
            .filter_by(company_id=company.id).first() is not None
        )
        news = (
            session.query(NewsSignal.id)
            .filter(NewsSignal.ticker == symbol).count()
        )
        return CompanySourcesOut(
            symbol=symbol,
            name=company.name,
            total_chunks=summary["total_chunks"],
            doc_types=[DocTypeSummary(**d) for d in summary["doc_types"]],
            has_financials=has_fin,
            has_price_history=has_prices,
            news_signals=news,
        )

    # ----------------------------------------------------------------- history
    def history(self, user_id: int, symbol: str | None, limit: int) -> list[ResearchHistoryItem]:
        items = []
        for row in get_research_history(user_id, symbol=symbol, limit=limit):
            try:
                sources = [SourceCitation(**s) for s in json.loads(row["sources_json"] or "[]")]
            except (json.JSONDecodeError, TypeError, ValueError):
                sources = []
            items.append(ResearchHistoryItem(
                id=row["id"], symbol=row["symbol"], mode=row["mode"],
                question=row["question"], answer=row["answer"],
                sources=sources, created_at=row["created_at"],
            ))
        return items


research_service = ResearchService()
