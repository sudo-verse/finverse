# Research Document Corpus

Drop company filings here and the AI Research Copilot will index them
(chunk → embed → store in ChromaDB with company/doc-type/year/page metadata).

## Layout

```
documents/
  RELIANCE/                  # NSE symbol, uppercase
    annual_reports/          # annual reports        (doc_type=annual_report)
    quarterly_reports/       # quarterly results     (doc_type=quarterly_report)
    earnings_calls/          # call transcripts      (doc_type=earnings_call)
    presentations/           # investor decks        (doc_type=presentation)
    announcements/           # NSE announcements     (doc_type=announcement)
    financials/              # financial statements  (doc_type=financials)
```

Supported formats: `.pdf` (page-aware — citations get real page numbers),
`.txt`, `.md`, `.html`. The year is inferred from the filename
(`RIL-Annual-Report-FY2024.pdf`, `Q4-2025-earnings-call.txt`, …).

## Indexing

```bash
python -m app.etl.ingest_documents              # everything (incremental)
python -m app.etl.ingest_documents RELIANCE     # one company
python -m app.etl.ingest_documents --news       # index Finverse news signals
```

Re-runs are incremental: `.ingested.json` tracks content hashes, so only new
or changed files are embedded. Files in this directory are also served at
`/docfiles/...` so source citations can open the original filing.
