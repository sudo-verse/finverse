"""Tests for text cleanup and the research retrieval helpers (pure logic)."""

from app.utils.text import strip_html
from app.genai import research as R


class TestStripHtml:
    def test_plain_text_passthrough(self):
        assert strip_html("TCS wins big deal") == "TCS wins big deal"

    def test_strips_tags_and_entities(self):
        assert strip_html('<a href="http://x">Hello</a> &amp; world') == "Hello & world"

    def test_handles_truncated_tag(self):
        assert strip_html('Reliance up <a href="https://news.goog') == "Reliance up"

    def test_none_and_empty(self):
        assert strip_html(None) == ""
        assert strip_html("") == ""


class TestTerms:
    def test_drops_stopwords_and_dedupes(self):
        terms = R._terms("Why is the Reliance company growing and growing?")
        assert "reliance" in terms and "growing" in terms
        assert "the" not in terms and "why" not in terms
        assert terms.count("growing") == 1


class TestWhere:
    def test_single_condition_is_flat(self):
        assert R._where(symbol="tcs") == {"symbol": "TCS"}

    def test_multiple_conditions_use_and(self):
        w = R._where(symbol="TCS", year=2024)
        assert "$and" in w and {"symbol": "TCS"} in w["$and"]

    def test_empty_is_none(self):
        assert R._where() is None


class TestFuse:
    def test_rrf_prefers_items_in_both_lists(self):
        a = [{"id": "x", "text": "", "meta": {}}, {"id": "y", "text": "", "meta": {}}]
        b = [{"id": "y", "text": "", "meta": {}}, {"id": "z", "text": "", "meta": {}}]
        fused = R._fuse(a, b)
        assert fused[0]["id"] == "y"  # appears in both → highest RRF score
        assert {c["id"] for c in fused} == {"x", "y", "z"}


class TestCompress:
    def test_short_text_untouched(self):
        assert R._compress("short text", ["short"]) == "short text"

    def test_keeps_matching_sentences(self):
        text = ("Irrelevant filler sentence here. " * 30
                + "Revenue grew 12 percent in fiscal 2024. "
                + "More filler follows this important line. " * 30)
        out = R._compress(text, ["revenue"], budget=300)
        assert "Revenue grew 12 percent" in out
        assert len(out) <= 300


class TestCitationLabel:
    def test_label_includes_type_year_page(self):
        label = R.citation_label({"source": "ril.pdf", "doc_type": "annual_report",
                                  "year": 2024, "page": 128})
        assert label == "Annual Report 2024, page 128 (ril.pdf)"
