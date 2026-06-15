"""Tests for the structural / table-aware / parent–child chunker (pure logic,
no embeddings or network)."""

from app.genai import chunking as C


class TestBuildHeader:
    def test_full_header(self):
        h = C.build_header("tcs", "annual_report", 2025, "Segment Results")
        assert h == "TCS · Annual Report 2025 · Segment Results"

    def test_minimal_header(self):
        assert C.build_header("TCS", None, None, None) == "TCS"

    def test_news_label(self):
        assert C.build_header("RELIANCE", "news", None, None) == "RELIANCE · News Signal"


class TestTableToMarkdown:
    def test_serialises_real_table(self):
        md = C._table_to_markdown([["Metric", "FY25"], ["Revenue", "267,021"]])
        assert "| Metric | FY25 |" in md
        assert "| --- | --- |" in md
        assert "| Revenue | 267,021 |" in md

    def test_rejects_single_row(self):
        assert C._table_to_markdown([["only", "header"]]) == ""

    def test_rejects_sparse_layout_grid(self):
        sparse = [["x", "", "", ""], ["", "", "", ""], ["", "", "y", ""]]
        assert C._table_to_markdown(sparse) == ""


class TestWindows:
    def test_sentence_aware_and_bounded(self):
        text = " ".join(f"Sentence number {i} about revenue and margins." for i in range(60))
        wins = C._windows(text)
        assert len(wins) > 1
        assert all(len(w) <= C.CHILD_SIZE + 200 for w in wins)  # ~bounded
        # no window starts mid-word from a hard character cut
        assert all(w == w.strip() for w in wins)

    def test_empty(self):
        assert C._windows("   ") == []


class TestChunkTextFile:
    def test_markdown_sections_become_parents(self, tmp_path):
        doc = tmp_path / "ACME_FY2025_annual_report.md"
        doc.write_text(
            "# Performance\n"
            "Revenue for FY2025 grew 18 percent to 12,450 crore rupees. "
            "Net profit rose to 1,820 crore.\n"
            "# Risks\n"
            "Demand depends on the infrastructure segment cycle.\n"
        )
        chunks, parents = C.chunk_file(str(doc), symbol="ACME",
                                       doc_type="annual_report", year=2025)
        assert chunks and parents
        # contextual header is embedded, clean body is stored
        assert all(c.embed_text.startswith("ACME · Annual Report 2025") for c in chunks)
        assert all(c.text in c.embed_text for c in chunks)
        # sections detected from headings
        sections = {c.section for c in chunks}
        assert "Performance" in sections and "Risks" in sections
        # every child references a real parent
        assert all(c.parent_id in parents for c in chunks)
        # parent holds the fuller text
        perf = next(c for c in chunks if c.section == "Performance")
        assert "12,450" in parents[perf.parent_id]["text"]
