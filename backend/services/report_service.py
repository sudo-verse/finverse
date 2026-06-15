"""GenAI endpoints — thin pass-throughs to the existing Gemini integrations:

  - investment report ... app.genai.report_generator.generate_report
                          (context assembly, prompt, DB cache all reused)
  - document Q&A ........ app.genai.rag.answer_question (ChromaDB + Gemini)
"""

import logging
import re
import uuid
from datetime import datetime, timezone

from app.db.database import get_session
from app.genai import gemini_client, research, semantic_cache
from app.genai.report_generator import generate_report
from backend.core.exceptions import NotFoundError, ServiceUnavailableError
from backend.schemas.report import ChatOut, ChatRequest, ChatSource, ReportOut, ReportRequest
from backend.services.sentiment_service import sentiment_service

logger = logging.getLogger("finverse.api")

# The assistant otherwise answers only from ingested documents (RAG), so
# market-wide questions like "top 5 stocks by sentiment score" have nothing to
# retrieve. Detect those and answer them from the structured sentiment_scores
# table instead — deterministic, grounded, and works without Gemini.
_RANK_RE = re.compile(
    r"\b(top|best|highest|strongest|leading|bullish|positive|"
    r"worst|lowest|weakest|bearish|negative|bottom|rank(?:ing|ed)?|leaderboard)\b"
)
_BOTTOM_RE = re.compile(r"\b(worst|lowest|weakest|bearish|negative|bottom)\b")
_NUM_RE = re.compile(r"\b(\d{1,2})\b")


def _is_leaderboard_query(message: str) -> bool:
    low = message.lower()
    return (("sentiment" in low or "score" in low)
            and _RANK_RE.search(low) is not None)


def _format_leaderboard(entries, order: str) -> str:
    if not entries:
        return (
            "I don't have any sentiment scores computed yet. Open the "
            "**Sentiment** page for a stock — or wait for the daily refresh — "
            "to populate the leaderboard, then ask me again."
        )
    title = "Top" if order == "top" else "Bottom"
    lines = [
        f"### {title} {len(entries)} NSE stocks by Finverse sentiment score\n",
        "| # | Stock | Score | Signal | Confidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for e in entries:
        stock = e.symbol + (f" — {e.name}" if e.name else "")
        conf = f"{round((e.confidence or 0) * 100)}%"
        lines.append(
            f"| {e.rank} | {stock} | **{e.overall:.1f}** | {e.recommendation or '—'} | {conf} |"
        )
    lines.append(
        "\n_Scores are the latest daily snapshot from Finverse's 5-pillar "
        "Sentiment Intelligence engine (0–100: technicals, fundamentals, news, "
        "ownership, market). Automated research, not investment advice._"
    )
    return "\n".join(lines)


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
        # Market-wide sentiment-ranking questions are answered from structured
        # data, not the document corpus (and need no Gemini key).
        if _is_leaderboard_query(payload.message):
            return self._leaderboard_chat(payload.message)

        _require_gemini()
        symbol = payload.symbol.upper() if payload.symbol else None

        def _serve(cached):
            logger.info("chat: cache hit (%s, symbol=%s)", cached["via"], symbol)
            return ChatOut(
                id=f"msg-{uuid.uuid4().hex[:12]}",
                content=cached["answer"],
                sources=[ChatSource(**s) for s in cached["sources"]],
                timestamp=datetime.now(timezone.utc),
            )

        # 1. Free exact-cache pre-check (no embedding).
        cached = semantic_cache.get(payload.message, symbol, record=False)
        if cached:
            return _serve(cached)

        # 2. Embed the query once — serves both the semantic-cache lookup and
        # (on a miss) the retrieval step, so a miss costs no extra embed.
        qvec = None
        try:
            qvec = gemini_client.embed([payload.message],
                                       task_type="RETRIEVAL_QUERY", max_retries=0)[0]
        except Exception:
            pass  # embeddings unavailable — skip semantic cache; retrieval → BM25
        if qvec is not None:
            cached = semantic_cache.get(payload.message, symbol, query_vec=qvec)
            if cached:
                return _serve(cached)

        # 3. Miss → advanced retrieval (hybrid + RRF + parent expansion +
        # compression) and generation; cache the result.
        sources, token_gen = research.research_answer(
            payload.message, symbol=symbol, k=payload.k, query_vec=qvec,
        )
        answer = "".join(token_gen)
        chat_sources = [
            ChatSource(source=research.citation_label(s),
                       snippet=(s.get("text") or "")[:240])
            for s in sources
        ]
        semantic_cache.put(payload.message, symbol, answer,
                           [s.model_dump() for s in chat_sources], query_vec=qvec)
        logger.info(
            "chat: answered via research pipeline with %d sources (symbol=%s)",
            len(sources), symbol,
        )
        return ChatOut(
            id=f"msg-{uuid.uuid4().hex[:12]}",
            content=answer,
            sources=chat_sources,
            timestamp=datetime.now(timezone.utc),
        )

    def _leaderboard_chat(self, message: str) -> ChatOut:
        low = message.lower()
        order = "bottom" if _BOTTOM_RE.search(low) else "top"
        match = _NUM_RE.search(low)
        limit = min(max(int(match.group(1)), 1), 20) if match else 5
        with get_session() as session:
            entries = sentiment_service.leaderboard(session, limit=limit, order=order)
        logger.info("chat: sentiment leaderboard (order=%s, limit=%d, returned=%d)",
                    order, limit, len(entries))
        return ChatOut(
            id=f"msg-{uuid.uuid4().hex[:12]}",
            content=_format_leaderboard(entries, order),
            sources=[],
            timestamp=datetime.now(timezone.utc),
        )


report_service = ReportService()
