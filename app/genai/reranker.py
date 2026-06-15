"""Cross-encoder reranker (self-hosted, via transformers).

Replaces the LLM reranker in the retrieval pipeline. A cross-encoder scores each
(query, passage) pair jointly, which orders precise matches far better than an
LLM asked to emit a ranking — and it's deterministic, cheaper, and faster (one
batched forward pass, no API call / quota). bge-reranker emits a single
relevance logit per pair.

Lazy-loaded and cached; the first call downloads the model (~280MB for
bge-reranker-base) to the HuggingFace cache. If torch/the model is unavailable
the caller falls back to the previous reranking path.
"""

import threading

from app.config import RERANKER_ENABLED, RERANKER_MODEL
from app.utils.logger import logger

_MAX_LEN = 512          # query+passage token budget per pair
_lock = threading.Lock()
_tok = None
_model = None
_unavailable = False    # set if loading fails, so we don't retry every call


def is_enabled() -> bool:
    return RERANKER_ENABLED and not _unavailable


def _load():
    global _tok, _model, _unavailable
    if _model is not None or _unavailable:
        return _tok, _model
    with _lock:
        if _model is None and not _unavailable:
            try:
                import torch  # noqa: F401
                from transformers import (
                    AutoModelForSequenceClassification,
                    AutoTokenizer,
                )

                logger.info("reranker: loading %s …", RERANKER_MODEL)
                _tok = AutoTokenizer.from_pretrained(RERANKER_MODEL)
                _model = AutoModelForSequenceClassification.from_pretrained(RERANKER_MODEL)
                _model.eval()
                logger.info("reranker: %s ready", RERANKER_MODEL)
            except Exception as e:
                _unavailable = True
                logger.warning("reranker: unavailable (%s); falling back", e)
    return _tok, _model


def score(query: str, passages: list[str]) -> list[float]:
    """Relevance score per passage for the query (higher = more relevant)."""
    import torch

    tok, model = _load()
    if model is None:
        raise RuntimeError("reranker unavailable")
    pairs = [[query, p or ""] for p in passages]
    with torch.no_grad():
        inputs = tok(pairs, padding=True, truncation=True,
                     max_length=_MAX_LEN, return_tensors="pt")
        logits = model(**inputs).logits.view(-1).float()
    return logits.tolist()


def rerank(query: str, candidates: list[dict], k: int) -> list[dict]:
    """Reorder candidates (each a dict with a 'text' key) by cross-encoder
    score and return the top k. Raises if the model is unavailable."""
    if not candidates:
        return []
    scores = score(query, [c.get("text", "") for c in candidates])
    ranked = sorted(zip(scores, candidates), key=lambda x: -x[0])
    return [c for _, c in ranked[:k]]
