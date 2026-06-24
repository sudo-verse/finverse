"""Query rewriting: JSON parsing, fallback robustness, and the disabled path."""

from app.genai import query_rewrite as qr


def _enable(monkeypatch, raw: str):
    monkeypatch.setattr(qr, "QUERY_REWRITE_ENABLED", True)
    monkeypatch.setattr(qr.gemini_client, "is_configured", lambda: True)
    monkeypatch.setattr(qr.gemini_client, "generate_text",
                        lambda *a, **k: raw)


class TestRewrite:
    def test_parses_json(self, monkeypatch):
        _enable(monkeypatch, """{
            "semantic_query": "TCS consolidated revenue fiscal 2026",
            "keyword_query": "TCS revenue 2026",
            "expansions": ["TCS FY26 sales", "Tata Consultancy revenue", "x"],
            "filters": {"company": "TCS", "year": 2026, "doc_type": null, "section": null}
        }""")
        rw = qr.rewrite("how much did tcs make last year?")
        assert rw.semantic_query == "TCS consolidated revenue fiscal 2026"
        assert "TCS revenue 2026" in rw.keyword_text
        assert len(rw.expansions) == 3
        assert rw.filters["year"] == 2026

    def test_handles_json_with_prose(self, monkeypatch):
        _enable(monkeypatch, 'Here you go:\n{"semantic_query":"a","keyword_query":"b"}')
        rw = qr.rewrite("q")
        assert rw.semantic_query == "a" and rw.keyword_query == "b"

    def test_falls_back_on_garbage(self, monkeypatch):
        _enable(monkeypatch, "sorry I cannot do that")
        rw = qr.rewrite("original question")
        assert rw.semantic_query == "original question"

    def test_falls_back_on_exception(self, monkeypatch):
        monkeypatch.setattr(qr, "QUERY_REWRITE_ENABLED", True)
        monkeypatch.setattr(qr.gemini_client, "is_configured", lambda: True)

        def _boom(*a, **k):
            raise RuntimeError("api down")

        monkeypatch.setattr(qr.gemini_client, "generate_text", _boom)
        rw = qr.rewrite("original question")
        assert rw.semantic_query == "original question"  # never raises

    def test_disabled_is_passthrough(self, monkeypatch):
        monkeypatch.setattr(qr, "QUERY_REWRITE_ENABLED", False)
        rw = qr.rewrite("my question")
        assert rw.semantic_query == "my question" and rw.expansions == []

    def test_expansions_capped_at_three(self, monkeypatch):
        _enable(monkeypatch, '{"semantic_query":"a","keyword_query":"b",'
                             '"expansions":["1","2","3","4","5"]}')
        assert len(qr.rewrite("q").expansions) == 3
