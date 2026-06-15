"""Retrieval-quality regression gate.

Runs the golden set through the live retrieval pipeline and fails if recall or
NDCG regress below the agreed floor. Deterministic (no LLM), so it can run in
CI on every change to chunking / embeddings / retrieval. Generation-quality
metrics (faithfulness, citation validity) need an API key and are exercised via
`python -m eval.run_eval --gen`, not in this gate.

Thresholds are intentionally a little below the current measured baseline so
they catch regressions without flaking. Re-baseline (raise them) after a proven
improvement.
"""

import pytest

from eval.run_eval import _is_relevant, _load, _ndcg, GOLDEN

K = 6
MIN_RECALL = 0.80   # ≥80% of questions must surface a relevant chunk in top-k
MIN_NDCG = 0.55     # rank quality floor


@pytest.fixture(scope="module")
def results():
    from app.genai import research

    items = _load(GOLDEN)
    out = []
    for it in items:
        sources = research.retrieve(it["question"], symbol=it.get("symbol"), k=K)
        rels = [1 if _is_relevant(s.get("text", ""), it["evidence_terms"]) else 0
                for s in sources]
        out.append((it["id"], rels))
    return out


def test_recall_floor(results):
    recall = sum(1 for _, rels in results if any(rels)) / len(results)
    misses = [i for i, rels in results if not any(rels)]
    assert recall >= MIN_RECALL, f"recall@{K}={recall:.2f} < {MIN_RECALL}; misses={misses}"


def test_ndcg_floor(results):
    ndcg = sum(_ndcg(rels) for _, rels in results) / len(results)
    assert ndcg >= MIN_NDCG, f"ndcg@{K}={ndcg:.2f} < {MIN_NDCG}"
