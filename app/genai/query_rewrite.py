"""Query understanding: rewrite a user question into retrieval-optimised forms.

Turns a conversational question into (a) a clean semantic query for the dense
arm, (b) a keyword query + alternate phrasings for the BM25 arm, and (c) any
metadata hints (company/year/doc-type/section). This widens recall on
conversational / multi-aspect questions before hybrid search runs.

Best-effort: any failure (no Gemini, bad JSON, timeout) falls back to the
original question, so retrieval never breaks because of the rewriter.
"""

import json
import re
from dataclasses import dataclass, field

from app.config import GEMINI_MODEL, QUERY_REWRITE_ENABLED
from app.genai import gemini_client
from app.utils.logger import logger

SYSTEM = (
    "You are a search optimization system for an equity-research RAG over NSE "
    "company filings. Rewrite the user's question into JSON with keys:\n"
    '  "semantic_query": a clean natural-language query for vector search,\n'
    '  "keyword_query": the key terms/tickers/figures for keyword search,\n'
    '  "expansions": up to 3 alternate phrasings (array of strings),\n'
    '  "filters": {"company": str|null, "year": int|null, '
    '"doc_type": str|null, "section": str|null}.\n'
    "Return ONLY the JSON object, no prose."
)


@dataclass
class RewrittenQuery:
    semantic_query: str
    keyword_query: str
    expansions: list[str] = field(default_factory=list)
    filters: dict = field(default_factory=dict)

    @property
    def keyword_text(self) -> str:
        """All lexical signal joined for the BM25 arm (terms get tokenised)."""
        return " ".join([self.keyword_query, *self.expansions]).strip()


def _passthrough(question: str) -> RewrittenQuery:
    return RewrittenQuery(semantic_query=question, keyword_query=question)


def enabled() -> bool:
    return QUERY_REWRITE_ENABLED and gemini_client.is_configured()


def rewrite(question: str) -> RewrittenQuery:
    if not enabled():
        return _passthrough(question)
    try:
        raw = gemini_client.generate_text(
            f"User question: {question}\n\nJSON:",
            system_instruction=SYSTEM, model=GEMINI_MODEL,
        )
        match = re.search(r"\{.*\}", raw or "", re.S)
        if not match:
            return _passthrough(question)
        data = json.loads(match.group(0))
        expansions = [str(e) for e in (data.get("expansions") or [])][:3]
        return RewrittenQuery(
            semantic_query=str(data.get("semantic_query") or question),
            keyword_query=str(data.get("keyword_query") or question),
            expansions=expansions,
            filters=data.get("filters") or {},
        )
    except Exception as e:
        logger.warning(f"query_rewrite: falling back to original ({e})")
        return _passthrough(question)
