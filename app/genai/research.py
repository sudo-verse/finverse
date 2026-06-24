"""Finverse AI Research Copilot — retrieval + generation pipeline.

Builds on the L9 RAG store (ChromaDB + Gemini embeddings) with a deeper
pipeline tuned for equity research over company filings:

  1. Hybrid search ....... semantic (vector) + keyword ($contains) candidates,
                           merged with reciprocal-rank fusion
  2. Metadata filtering .. company symbol / document type / year
  3. Reranking ........... Gemini orders the fused candidates by relevance
  4. Compression ......... query-aware sentence pruning before generation

Generation is grounded in the retrieved excerpts plus Finverse's structured
data (fundamentals, quant metrics, peers, news signals) and produces
analyst-style answers with numbered [n] citations. All generation entry
points are generators so the API layer can stream tokens.
"""

import json
import re

from app.genai import gemini_client
from app.genai.rag import get_collection
from app.utils.logger import logger

# How wide to cast the net before the cross-encoder narrows it down. A bigger
# pool gives the reranker more to work with (retrieve ~30 → rerank → top k).
SEMANTIC_CANDIDATES = 24
KEYWORD_CANDIDATES = 15
RERANK_INPUT_MAX = 30
DEFAULT_TOP_K = 6
# Token budget guards (chars ~ 4x tokens). The per-chunk budget is generous
# because parent expansion hands back page-level sections we don't want to
# over-prune.
CHUNK_CHAR_BUDGET = 1400
CONTEXT_CHAR_BUDGET = 9000
STRUCTURED_CHAR_BUDGET = 6000
_NUM_RE_C = re.compile(r"\d")  # finance answers are numbers — never prune them

DOC_TYPE_LABELS = {
    "annual_report": "Annual Report",
    "quarterly_report": "Quarterly Report",
    "earnings_call": "Earnings Call",
    "presentation": "Investor Presentation",
    "announcement": "NSE Announcement",
    "financials": "Financial Statements",
    "news": "News Signal",
}

_STOPWORDS = frozenset(
    "a an and are as at be but by did do does for from had has have how in is "
    "it its latest of on or that the their this to was were what when which "
    "who why will with about company stock share me i you your".split()
)

_SENT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9&.-]{2,}")


def _terms(text: str) -> list[str]:
    """Meaningful lowercase query terms (stopwords removed, deduped, in order)."""
    seen, out = set(), []
    for w in _WORD_RE.findall(text.lower()):
        if w not in _STOPWORDS and w not in seen:
            seen.add(w)
            out.append(w)
    return out


def _where(symbol: str = None, doc_type: str = None, year: int = None):
    """Chroma metadata filter; multiple conditions need an explicit $and."""
    conds = []
    if symbol:
        conds.append({"symbol": symbol.upper()})
    if doc_type:
        conds.append({"doc_type": doc_type})
    if year:
        conds.append({"year": int(year)})
    if not conds:
        return None
    return conds[0] if len(conds) == 1 else {"$and": conds}


# ---------------------------------------------------------------------------
# 1+2. Hybrid retrieval with metadata filtering
# ---------------------------------------------------------------------------

def _semantic_candidates(question: str, where, query_vec=None) -> list[dict]:
    collection = get_collection()
    try:
        # Reuse a caller-supplied embedding (e.g. from the semantic-cache lookup)
        # to avoid embedding the query twice. Otherwise embed now, failing fast
        # on the query path — don't inherit ingestion's long 429 backoff;
        # degrade to keyword retrieval instead of stalling the user.
        q_vec = query_vec if query_vec is not None else gemini_client.embed(
            [question], task_type="RETRIEVAL_QUERY", max_retries=0
        )[0]
    except Exception as e:
        # Embedding provider unavailable (e.g. quota/429). Degrade to the BM25
        # (keyword) arm rather than failing the whole query — the lexical arm
        # needs no embeddings, so retrieval stays useful.
        logger.warning(f"research: semantic arm unavailable ({e}); keyword-only")
        return []
    res = collection.query(
        query_embeddings=[q_vec], n_results=SEMANTIC_CANDIDATES, where=where
    )
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    ids = res.get("ids", [[]])[0]
    return [
        {"id": i, "text": d, "meta": m or {}}
        for i, d, m in zip(ids, docs, metas)
    ]


def _keyword_candidates(question: str, where) -> list[dict]:
    """Exact-term matches the embedding may miss (tickers, figures, names).

    Uses a correct, case-insensitive BM25 index (app.genai.lexical) rather than
    Chroma's case-sensitive `$contains`, which silently failed on real
    original-case filing text."""
    try:
        from app.genai.lexical import get_index

        return get_index().search(question, KEYWORD_CANDIDATES, where=where)
    except Exception as e:
        logger.warning(f"research: keyword search failed ({e}); semantic only")
        return []


def _fuse(semantic: list[dict], keyword: list[dict]) -> list[dict]:
    """Reciprocal-rank fusion of the two candidate lists."""
    K = 60  # standard RRF damping constant
    scores: dict[str, float] = {}
    by_id: dict[str, dict] = {}
    for rank_list in (semantic, keyword):
        for rank, cand in enumerate(rank_list):
            scores[cand["id"]] = scores.get(cand["id"], 0.0) + 1.0 / (K + rank)
            by_id.setdefault(cand["id"], cand)
    ordered = sorted(scores, key=lambda i: -scores[i])
    return [by_id[i] for i in ordered[:RERANK_INPUT_MAX]]


# ---------------------------------------------------------------------------
# 3. Reranking
# ---------------------------------------------------------------------------
# Cross-encoder reranking is RRF-fused with the incoming lexical/semantic order
# rather than replacing it. Measured on our golden set, a *pure* cross-encoder
# reorder (and the old LLM reranker) demoted exact-figure chunks that lexical
# fusion ranks correctly, hurting recall/NDCG. Blending preserves strong matches
# while letting the cross-encoder refine. The plain fused order is already
# strong on a figure-heavy corpus, so the reranker is opt-in (RERANKER_ENABLED);
# when off, we trust the RRF fusion order directly. The previous Gemini LLM
# reranker is retired — slower, costly, nondeterministic, and measurably worse
# than no rerank.


def _rerank(question: str, candidates: list[dict], k: int) -> list[dict]:
    if len(candidates) <= k:
        return candidates

    from app.genai import reranker

    if reranker.is_enabled():
        try:
            ce_scores = reranker.score(question, [c["text"] for c in candidates])
            ce_order = sorted(range(len(candidates)), key=lambda i: -ce_scores[i])
            ce_rank = {idx: r for r, idx in enumerate(ce_order)}
            K = 60  # candidates already arrive in fused (RRF) order → index = rank
            blended = sorted(range(len(candidates)),
                             key=lambda i: -(1.0 / (K + i) + 1.0 / (K + ce_rank[i])))
            return [candidates[i] for i in blended[:k]]
        except Exception as e:
            logger.warning(f"research: cross-encoder rerank failed ({e}); fused order")
    return candidates[:k]  # trust the lexical+semantic RRF fusion order


# ---------------------------------------------------------------------------
# 4. Query-aware context compression
# ---------------------------------------------------------------------------

def _compress(text: str, terms: list[str], budget: int = CHUNK_CHAR_BUDGET) -> str:
    """Keep the sentences that matter for the query (plus leading context)
    instead of sending whole chunks to the model."""
    if len(text) <= budget:
        return text
    sentences = _SENT_RE.split(text)
    keep = set()
    for i, s in enumerate(sentences):
        low = s.lower()
        # Keep query-term matches and any sentence carrying figures — in an
        # equity-research corpus the numbers are usually the answer.
        if any(t in low for t in terms) or _NUM_RE_C.search(s):
            keep.update({i - 1, i, i + 1})  # neighbours preserve flow
    if not keep:
        return text[:budget]
    out, last = [], None
    for i in sorted(x for x in keep if 0 <= x < len(sentences)):
        if last is not None and i != last + 1:
            out.append("…")
        out.append(sentences[i].strip())
        last = i
    return " ".join(out)[:budget]


# ---------------------------------------------------------------------------
# Retrieval entry point
# ---------------------------------------------------------------------------

def retrieve(question: str, symbol: str = None, doc_type: str = None,
             year: int = None, k: int = DEFAULT_TOP_K, query_vec=None) -> list[dict]:
    """Full pipeline → list of {id, text, source, doc_type, year, page}."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    where = _where(symbol, doc_type, year)
    # Query understanding: expand into semantic + keyword forms (skipped when a
    # precomputed query_vec is supplied, i.e. the cache path). Falls back to the
    # raw question if rewriting is disabled/unavailable.
    from app.genai import query_rewrite

    rw = query_rewrite.rewrite(question) if query_vec is None else None
    semantic_q = rw.semantic_query if rw else question
    keyword_q = rw.keyword_text if rw else question

    semantic = _semantic_candidates(semantic_q, where, query_vec=query_vec)
    keyword = _keyword_candidates(keyword_q, where)
    fused = _fuse(semantic, keyword)
    if not fused:
        return []
    top = _rerank(question, fused, k)

    # Small-to-big: we matched on precise child chunks; hand the generator the
    # fuller parent section. Children of the same parent consolidate into one
    # source. Falls back to the child text when no parent exists (legacy corpus).
    from app.genai import parent_store

    terms = _terms(question)
    results = []
    seen_parents = set()
    for c in top:
        m = c["meta"]
        text = c["text"]
        pid = m.get("parent_id")
        if pid:
            if pid in seen_parents:
                continue
            parent = parent_store.get(pid)
            if parent and parent.get("text"):
                seen_parents.add(pid)
                text = parent["text"]
        results.append({
            "id": c["id"],
            "text": _compress(text, terms),
            "source": m.get("source", "document"),
            "doc_type": m.get("doc_type"),
            "year": m.get("year"),
            "page": m.get("page"),
            "section": m.get("section"),
        })
    return results


def citation_label(src: dict) -> str:
    label = DOC_TYPE_LABELS.get(src.get("doc_type") or "", "") or src["source"]
    if src.get("year"):
        label += f" {src['year']}"
    if src.get("page"):
        label += f", page {src['page']}"
    if src.get("section"):
        label += f" — {src['section']}"
    if label != src["source"]:
        label += f" ({src['source']})"
    return label


def _context_block(sources: list[dict], offset: int = 0) -> str:
    parts, used = [], 0
    for i, s in enumerate(sources):
        block = f"[{offset + i + 1}] {citation_label(s)}\n{s['text']}"
        if used + len(block) > CONTEXT_CHAR_BUDGET:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)


def _structured_block(structured: dict | None) -> str:
    if not structured:
        return ""
    blob = json.dumps(structured, default=str)
    if len(blob) > STRUCTURED_CHAR_BUDGET:
        blob = blob[:STRUCTURED_CHAR_BUDGET] + "…(truncated)"
    return (
        "\n\n=== FINVERSE STRUCTURED DATA (live metrics, fundamentals, peers, "
        "news signals — cite as [Finverse data]) ===\n" + blob
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

ANALYST_SYSTEM = (
    "You are the Finverse AI Research Copilot — a senior equity research "
    "analyst covering NSE-listed Indian companies. Answer using ONLY the "
    "numbered document excerpts and the Finverse structured data provided. "
    "Never invent figures; if something is not in the material, say so.\n\n"
    "Citations: when a claim comes from excerpt [n], append [n] to the "
    "sentence. Cite structured data as [Finverse data].\n\n"
    "For substantial research questions, structure the answer in Markdown as:\n"
    "## Executive Summary\n## Key Findings\n## Evidence from Documents\n"
    "## Risks\n## Investment Implications\n\n"
    "For quick factual questions, reply concisely without the full template. "
    "If the user asks for a beginner explanation, use plain language and "
    "analogies. Use Indian conventions (₹, Cr, Lakh). End substantial "
    "answers with a one-line italic disclaimer that this is automated "
    "research, not investment advice."
)

COMPARE_SYSTEM = (
    "You are the Finverse AI Research Copilot in comparison mode — a senior "
    "equity research analyst. Compare the companies using ONLY the provided "
    "excerpts and structured data, citing excerpts as [n] and structured "
    "data as [Finverse data]. Structure the answer in Markdown as:\n"
    "## Executive Summary\n## Head-to-Head (use a Markdown table)\n"
    "## Strengths & Weaknesses\n## Risks\n## Verdict\n\n"
    "Be balanced and evidence-based; flag missing data instead of guessing. "
    "End with a one-line italic disclaimer that this is automated research, "
    "not investment advice."
)


def _history_block(history: list[dict] | None) -> str:
    if not history:
        return ""
    turns = history[-6:]  # short rolling window keeps the prompt lean
    lines = [f"{'User' if t.get('role') == 'user' else 'Analyst'}: {t.get('content', '')[:500]}"
             for t in turns]
    return "\n\n=== CONVERSATION SO FAR ===\n" + "\n".join(lines)


def research_answer(question: str, symbol: str = None, history: list[dict] = None,
                    structured: dict = None, doc_type: str = None,
                    year: int = None, k: int = DEFAULT_TOP_K, query_vec=None):
    """Returns (sources, token_generator). Sources are resolved before
    generation starts so the API can emit them ahead of the streamed answer."""
    sources = retrieve(question, symbol=symbol, doc_type=doc_type, year=year,
                       k=k, query_vec=query_vec)

    scope = f" about {symbol}" if symbol else ""
    excerpts = _context_block(sources) if sources else "(no document excerpts matched)"
    prompt = (
        f"Question{scope}: {question}\n"
        f"{_history_block(history)}\n\n"
        f"=== DOCUMENT EXCERPTS ===\n{excerpts}"
        f"{_structured_block(structured)}\n\n"
        f"Answer:"
    )
    return sources, gemini_client.generate_stream(prompt, system_instruction=ANALYST_SYSTEM)


def research_compare(symbols: list[str], question: str = None,
                     structured: dict = None, k: int = 4):
    """Comparison mode: retrieve per company, then one comparative answer.

    Returns (sources, token_generator); sources are tagged with their symbol.
    """
    question = question or f"Compare {' and '.join(symbols)} as investments."
    all_sources: list[dict] = []
    blocks = []
    for sym in symbols:
        srcs = retrieve(question, symbol=sym, k=k)
        for s in srcs:
            s["symbol"] = sym
        block = _context_block(srcs, offset=len(all_sources))
        blocks.append(f"--- Documents for {sym} ---\n{block or '(none found)'}")
        all_sources.extend(srcs)

    prompt = (
        f"Comparison request: {question}\n"
        f"Companies: {', '.join(symbols)}\n\n"
        f"=== DOCUMENT EXCERPTS ===\n" + "\n\n".join(blocks) +
        f"{_structured_block(structured)}\n\n"
        f"Comparison report:"
    )
    return all_sources, gemini_client.generate_stream(prompt, system_instruction=COMPARE_SYSTEM)


# ---------------------------------------------------------------------------
# Corpus introspection (powers the "Available Sources" panel)
# ---------------------------------------------------------------------------

def source_summary(symbol: str) -> dict:
    """Aggregate the indexed corpus for one company by doc_type/year."""
    collection = get_collection()
    res = collection.get(where={"symbol": symbol.upper()}, include=["metadatas"])
    metas = res.get("metadatas") or []

    by_type: dict[str, dict] = {}
    for m in metas:
        dt = (m or {}).get("doc_type") or "other"
        entry = by_type.setdefault(dt, {"chunks": 0, "years": set(), "sources": set()})
        entry["chunks"] += 1
        if m.get("year"):
            entry["years"].add(int(m["year"]))
        entry["sources"].add(m.get("source", "?"))

    return {
        "total_chunks": len(metas),
        "doc_types": [
            {
                "doc_type": dt,
                "label": DOC_TYPE_LABELS.get(dt, dt.replace("_", " ").title()),
                "chunks": v["chunks"],
                "documents": len(v["sources"]),
                "years": sorted(v["years"], reverse=True),
            }
            for dt, v in sorted(by_type.items())
        ],
    }


def symbols_with_documents() -> dict[str, int]:
    """{symbol: chunk_count} for every company present in the vector store."""
    collection = get_collection()
    if collection.count() == 0:
        return {}
    res = collection.get(include=["metadatas"])
    counts: dict[str, int] = {}
    for m in res.get("metadatas") or []:
        sym = (m or {}).get("symbol")
        if sym:
            counts[sym] = counts.get(sym, 0) + 1
    return counts
