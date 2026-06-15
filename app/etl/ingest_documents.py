"""Document ingestion pipeline for the AI Research Copilot.

Watches a conventional folder layout and indexes everything into the RAG
vector store (chunk → embed → upsert) with research-grade metadata
(company, doc_type, year, source, page_number):

    documents/
      RELIANCE/
        annual_reports/      -> doc_type=annual_report
        quarterly_reports/   -> doc_type=quarterly_report
        earnings_calls/      -> doc_type=earnings_call
        presentations/       -> doc_type=presentation
        announcements/       -> doc_type=announcement
        financials/          -> doc_type=financials

Supported files: .pdf (page-aware), .txt, .md, .html.
A manifest of content hashes makes re-runs incremental — only new or
changed files are embedded (embedding calls cost money).

Usage:
    python -m app.etl.ingest_documents                 # whole documents/ tree
    python -m app.etl.ingest_documents RELIANCE        # one company
    python -m app.etl.ingest_documents --news          # index DB news signals
"""

import hashlib
import json
import os
import re
import sys

from app.genai.rag import ingest_file, ingest_text
from app.utils.logger import logger

DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "documents")
MANIFEST = os.path.join(DOCUMENTS_DIR, ".ingested.json")

FOLDER_DOC_TYPES = {
    "annual_reports": "annual_report",
    "quarterly_reports": "quarterly_report",
    "earnings_calls": "earnings_call",
    "presentations": "presentation",
    "announcements": "announcement",
    "financials": "financials",
}

SUPPORTED_EXT = (".pdf", ".txt", ".md", ".html")

# FY24 / FY2024 / 2024 anywhere in the filename
_YEAR_RE = re.compile(r"(?:FY[\s_-]?(\d{2,4})|(20\d{2}))", re.IGNORECASE)


def infer_year(filename: str) -> int | None:
    m = _YEAR_RE.search(filename)
    if not m:
        return None
    if m.group(2):
        return int(m.group(2))
    fy = int(m.group(1))
    return fy if fy > 100 else 2000 + fy


def _load_manifest() -> dict:
    try:
        with open(MANIFEST) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_manifest(manifest: dict) -> None:
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def _file_hash(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


def ingest_documents(symbol: str = None) -> dict:
    """Walk documents/ (optionally one company) and index new/changed files.

    Returns {files, chunks, skipped}.
    """
    if not os.path.isdir(DOCUMENTS_DIR):
        logger.warning(f"ingest: no '{DOCUMENTS_DIR}/' directory found")
        return {"files": 0, "chunks": 0, "skipped": 0}

    manifest = _load_manifest()
    files = chunks = skipped = 0

    companies = [symbol.upper()] if symbol else sorted(os.listdir(DOCUMENTS_DIR))
    for company in companies:
        company_dir = os.path.join(DOCUMENTS_DIR, company)
        if not os.path.isdir(company_dir):
            continue
        for folder, doc_type in FOLDER_DOC_TYPES.items():
            folder_path = os.path.join(company_dir, folder)
            if not os.path.isdir(folder_path):
                continue
            for name in sorted(os.listdir(folder_path)):
                path = os.path.join(folder_path, name)
                if not name.lower().endswith(SUPPORTED_EXT) or not os.path.isfile(path):
                    continue
                digest = _file_hash(path)
                key = f"{company}/{folder}/{name}"
                if manifest.get(key) == digest:
                    skipped += 1
                    continue
                logger.info(f"ingest: {key} ({doc_type})")
                n = ingest_file(path, symbol=company, doc_type=doc_type,
                                year=infer_year(name))
                manifest[key] = digest
                _save_manifest(manifest)  # checkpoint per file (embeds are paid)
                files += 1
                chunks += n

    logger.info(f"ingest: done — {files} files, {chunks} chunks, {skipped} unchanged")
    return {"files": files, "chunks": chunks, "skipped": skipped}


def ingest_news_signals(symbol: str = None, limit: int = 300) -> int:
    """Index the engine's scored news signals so the copilot can reason over
    recent news flow alongside filings."""
    from app.db.database import get_session
    from app.db.models import NewsSignal

    with get_session() as session:
        q = session.query(NewsSignal).order_by(NewsSignal.id.desc())
        if symbol:
            q = q.filter(NewsSignal.ticker == symbol.upper())
        rows = q.limit(limit).all()
        items = [
            (r.ticker, r.id,
             f"News ({r.source}, {r.published_at}): {r.news} "
             f"[event={r.event}, sentiment={r.sentiment_label}, signal={r.signal}]")
            for r in rows if r.ticker and r.news
        ]

    chunks = 0
    for ticker, sig_id, text in items:
        chunks += ingest_text(text, source=f"news-signal-{sig_id}",
                              symbol=ticker, doc_type="news")
    logger.info(f"ingest: indexed {len(items)} news signals ({chunks} chunks)")
    return chunks


def reindex() -> dict:
    """Full rebuild for a chunking-scheme change: wipe the vector store, parent
    store and manifest, then re-ingest all documents + news from scratch.

    Resumable — if the daily embedding quota interrupts the run, re-running
    continues from where Chroma already has chunks (ids are deterministic and
    upserts are idempotent), so only the wipe happens once.
    """
    from app.genai import lexical, parent_store, rag

    logger.warning("ingest: REINDEX — wiping vector store, parents and manifest")
    rag.reset_collection()
    parent_store.clear()
    lexical.invalidate()
    try:
        os.remove(MANIFEST)
    except FileNotFoundError:
        pass

    result = ingest_documents()
    result["news_chunks"] = ingest_news_signals()
    logger.info("ingest: reindex complete — %s", result)
    return result


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    if "--reindex" in args:
        reindex()
    elif "--news" in args:
        args.remove("--news")
        ingest_news_signals(args[0] if args else None)
    else:
        ingest_documents(args[0] if args else None)
