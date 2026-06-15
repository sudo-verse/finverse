"""Tests for the semantic answer cache (pure logic; vectors are hand-supplied,
so no embedding/network)."""

import pytest

from app.genai import semantic_cache as sc


@pytest.fixture(autouse=True)
def _clear():
    sc.clear()
    yield
    sc.clear()


def test_exact_hit_ignores_case_and_punctuation():
    sc.put("What are the risks?", "TCS", "Risk answer", [{"source": "AR", "snippet": "x"}])
    hit = sc.get("  what are THE risks  ", "TCS")
    assert hit and hit["answer"] == "Risk answer" and hit["via"] == "exact"


def test_symbol_scoping_prevents_cross_company_hits():
    sc.put("What are the risks?", "TCS", "TCS risks", [])
    assert sc.get("What are the risks?", "INFY") is None


def test_semantic_hit_on_similar_vector():
    sc.put("revenue growth", "TCS", "Grew 4.6%", [], query_vec=[1.0, 0.0, 0.0])
    hit = sc.get("how did revenue grow", "TCS", query_vec=[0.99, 0.1, 0.0])
    assert hit and hit["answer"] == "Grew 4.6%" and hit["via"].startswith("semantic")


def test_semantic_miss_on_dissimilar_vector():
    sc.put("revenue growth", "TCS", "Grew 4.6%", [], query_vec=[1.0, 0.0, 0.0])
    assert sc.get("board composition", "TCS", query_vec=[0.0, 1.0, 0.0]) is None


def test_lru_eviction_respects_cap(monkeypatch):
    monkeypatch.setattr(sc, "MAX_ENTRIES", 3)
    for i in range(5):
        sc.put(f"q{i}", "TCS", f"a{i}", [])
    assert sc.stats()["entries"] == 3
    assert sc.get("q0", "TCS") is None    # evicted
    assert sc.get("q4", "TCS")["answer"] == "a4"  # kept


def test_stats_track_hits_and_misses():
    sc.put("q", "TCS", "a", [])
    sc.get("q", "TCS")        # hit
    sc.get("other", "TCS")    # miss
    s = sc.stats()
    assert s["hits"] == 1 and s["misses"] == 1 and s["hit_rate"] == 0.5
