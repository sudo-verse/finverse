"""In-memory BM25 sparse retrieval over the Chroma document corpus.

Why this exists: Chroma's `where_document={"$contains": term}` filter is a
*case-sensitive* substring match. The research pipeline lowercases query terms,
so "reliance" never matched "Reliance Industries" in the original-case filing
text — the lexical arm of "hybrid" search was silently returning nothing and
RRF collapsed to semantic-only. This module replaces that with a correct,
case-insensitive Okapi BM25 index built from the same chunks: real TF-IDF term
weighting instead of substring presence, scoped by the same metadata filters.

The index is cached and rebuilt only when the corpus size changes, so the
per-query cost is just tokenizing the query and scoring candidate docs.
"""

import math
import re
import threading

from app.genai.rag import get_collection

# Tokens: alphanumerics plus the punctuation common in tickers/figures (TCS,
# 12,450, Q4-FY25, P&L). Lowercased so matching is case-insensitive.
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9&.\-]*")

# Standard Okapi BM25 parameters.
_K1 = 1.5
_B = 0.75


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall((text or "").lower())


def _match(meta: dict, where: dict | None) -> bool:
    """Evaluate the same metadata filter shapes app.genai.research._where emits
    (a single {key: value} or an {"$and": [...]} of them)."""
    if not where:
        return True
    if "$and" in where:
        return all(_match(meta, cond) for cond in where["$and"])
    return all((meta or {}).get(k) == v for k, v in where.items())


class BM25Index:
    def __init__(self, ids: list[str], docs: list[str], metas: list[dict]):
        self.ids = ids
        self.docs = docs
        self.metas = metas
        self.N = len(docs)

        self._tf: list[dict[str, int]] = []
        self._len: list[int] = []
        self._df: dict[str, int] = {}
        for d in docs:
            toks = _tokenize(d)
            self._len.append(len(toks))
            tf: dict[str, int] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            self._tf.append(tf)
            for t in tf:  # document frequency uses unique terms per doc
                self._df[t] = self._df.get(t, 0) + 1
        self._avgdl = (sum(self._len) / self.N) if self.N else 0.0

    def _idf(self, term: str) -> float:
        n = self._df.get(term, 0)
        # BM25+ idf form — strictly positive, avoids penalising frequent terms.
        return math.log(1 + (self.N - n + 0.5) / (n + 0.5))

    def search(self, query: str, k: int, where: dict | None = None) -> list[dict]:
        q_terms = set(_tokenize(query))
        if not q_terms or not self.N:
            return []
        scored: list[tuple[float, int]] = []
        for i in range(self.N):
            if where and not _match(self.metas[i], where):
                continue
            tf, dl = self._tf[i], self._len[i]
            score = 0.0
            for t in q_terms:
                f = tf.get(t, 0)
                if not f:
                    continue
                denom = f + _K1 * (1 - _B + _B * dl / (self._avgdl or 1.0))
                score += self._idf(t) * (f * (_K1 + 1)) / denom
            if score > 0:
                scored.append((score, i))
        scored.sort(key=lambda x: -x[0])
        return [
            {"id": self.ids[i], "text": self.docs[i], "meta": self.metas[i] or {}}
            for _, i in scored[:k]
        ]


_lock = threading.Lock()
_index: BM25Index | None = None
_index_count: int = -1


def get_index() -> BM25Index:
    """Cached BM25 index over the document collection. Rebuilds when the corpus
    size changes (cheap for our scale; a larger corpus would warrant a persisted
    sparse index instead)."""
    global _index, _index_count
    col = get_collection()
    count = col.count()
    with _lock:
        if _index is None or count != _index_count:
            res = col.get(include=["documents", "metadatas"])
            _index = BM25Index(
                res.get("ids") or [],
                res.get("documents") or [],
                res.get("metadatas") or [],
            )
            _index_count = count
        return _index


def invalidate() -> None:
    """Force a rebuild on next search (call after re-ingesting documents)."""
    global _index, _index_count
    with _lock:
        _index, _index_count = None, -1
