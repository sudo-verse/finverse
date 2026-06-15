"""Semantic cache for the research/chat answer path.

Finance users ask the same things repeatedly ("what are the risks?", "revenue
growth?") in slightly different words. This caches answers keyed by query
*meaning*, not exact text, so a paraphrase is served from cache — skipping the
expensive retrieval + rerank + generation entirely.

Lookup is two-tier:
  1. exact (normalised string) — free, instant, no embedding.
  2. semantic — embed the query (RETRIEVAL_QUERY) and cosine-match cached
     queries within the same symbol scope above a similarity threshold.

In-memory, TTL + LRU bounded. Entries are scoped by (symbol) so a question
about one company can't be answered from another's cached answer.
"""

import re
import threading
import time
from collections import OrderedDict

from app.utils.logger import logger

SIM_THRESHOLD = 0.94     # cosine ≥ this counts as the same question
TTL_SECONDS = 3600       # answers go stale (news/prices move) — 1h default
MAX_ENTRIES = 256

_lock = threading.Lock()
_store: "OrderedDict[str, dict]" = OrderedDict()  # key -> entry
_hits = _misses = 0


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower()).rstrip("?.! ")


def _key(symbol: str | None, norm_q: str) -> str:
    return f"{(symbol or '*').upper()}::{norm_q}"


def _cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _evict_expired(now: float) -> None:
    for k in [k for k, e in _store.items() if now - e["ts"] > TTL_SECONDS]:
        _store.pop(k, None)


def stats() -> dict:
    total = _hits + _misses
    return {"entries": len(_store), "hits": _hits, "misses": _misses,
            "hit_rate": round(_hits / total, 3) if total else 0.0}


def get(question: str, symbol: str | None, query_vec=None,
        record: bool = True) -> dict | None:
    """Return a cached {answer, sources} for an equivalent question, or None.

    Pass `query_vec` (the query embedding the caller already computed) to enable
    the semantic tier without a second embed call. Callers can do a free
    exact-only pre-check first (query_vec=None) and embed only on a miss; pass
    `record=False` on that pre-check so it isn't counted as a miss.
    """
    global _hits, _misses
    now = time.time()
    norm = _norm(question)
    with _lock:
        _evict_expired(now)
        # 1. exact normalised match (free — no embedding needed)
        entry = _store.get(_key(symbol, norm))
        if entry:
            _store.move_to_end(_key(symbol, norm))
            _hits += 1
            return {"answer": entry["answer"], "sources": entry["sources"], "via": "exact"}
        # 2. semantic match within the same symbol scope
        if query_vec is not None:
            best, best_sim = None, 0.0
            scope = (symbol or "*").upper()
            for e in _store.values():
                if e["scope"] != scope or e.get("vec") is None:
                    continue
                sim = _cosine(query_vec, e["vec"])
                if sim > best_sim:
                    best, best_sim = e, sim
            if best and best_sim >= SIM_THRESHOLD:
                _hits += 1
                return {"answer": best["answer"], "sources": best["sources"],
                        "via": f"semantic({best_sim:.3f})"}
        if record:
            _misses += 1
        return None


def put(question: str, symbol: str | None, answer: str, sources: list,
        query_vec=None) -> None:
    if not answer:
        return
    norm = _norm(question)
    with _lock:
        _store[_key(symbol, norm)] = {
            "answer": answer, "sources": sources, "ts": time.time(),
            "scope": (symbol or "*").upper(), "vec": query_vec,
        }
        _store.move_to_end(_key(symbol, norm))
        while len(_store) > MAX_ENTRIES:
            _store.popitem(last=False)  # LRU eviction


def clear() -> None:
    global _hits, _misses
    with _lock:
        _store.clear()
        _hits = _misses = 0
    logger.info("semantic_cache: cleared")
