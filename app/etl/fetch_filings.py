"""Fetch company filings from NSE into the research corpus.

Downloads annual report PDFs (NSE getCorpAnnualReport) into the
documents/<SYMBOL>/annual_reports/ layout and indexes them through the
standard ingestion pipeline (chunk → embed → ChromaDB with page metadata),
making them citable by the AI Research Copilot.

Embedding costs money, so the default is the LATEST report only.

Usage:
    python -m app.etl.fetch_filings RELIANCE            # latest annual report
    python -m app.etl.fetch_filings RELIANCE --all      # every listed year
    python -m app.etl.fetch_filings RELIANCE --no-index # download only
"""

import os
import re
import sys

from app.etl.ingest_documents import DOCUMENTS_DIR, ingest_documents
from app.market.nse_client import NSEClient
from app.utils.logger import logger


def _safe_name(symbol: str, from_year, to_year, url: str) -> str:
    ext = os.path.splitext(url.split("?")[0])[1] or ".pdf"
    years = f"{from_year or ''}-{to_year or ''}".strip("-") or "latest"
    return re.sub(r"[^A-Za-z0-9._-]", "_", f"{symbol}-annual-report-{years}{ext}")


def fetch_annual_reports(symbol: str, all_years: bool = False, index: bool = True) -> int:
    """Download (and optionally index) annual reports. Returns #files saved."""
    symbol = symbol.upper()
    client = NSEClient()
    data = client.quote_api("getCorpAnnualReport", symbol=symbol,
                            marketApiType="equities", noOfRecords=20)
    # this NSE endpoint returns a top-level JSON list
    rows = data if isinstance(data, list) else (data or {}).get("data") or []
    if not rows:
        logger.warning(f"fetch_filings: no annual reports listed for {symbol}")
        return 0
    if not all_years:
        rows = rows[:1]  # newest first per NSE

    target_dir = os.path.join(DOCUMENTS_DIR, symbol, "annual_reports")
    os.makedirs(target_dir, exist_ok=True)

    saved = 0
    for row in rows:
        url = row.get("fileName")
        if not url:
            continue
        path = os.path.join(target_dir, _safe_name(symbol, row.get("fromYr"), row.get("toYr"), url))
        if os.path.exists(path) and os.path.getsize(path) > 0:
            logger.info(f"fetch_filings: already downloaded {os.path.basename(path)}")
            continue
        logger.info(f"fetch_filings: downloading {url}")
        try:
            # the client session carries the NSE cookie handshake
            res = client.session.get(url, headers=client.headers, timeout=120, stream=True)
            res.raise_for_status()
            tmp = path + ".part"
            with open(tmp, "wb") as f:
                for chunk in res.iter_content(1 << 16):
                    f.write(chunk)
            os.replace(tmp, path)
            size_mb = os.path.getsize(path) / 1e6
            logger.info(f"fetch_filings: saved {os.path.basename(path)} ({size_mb:.1f} MB)")
            saved += 1
        except Exception as e:
            logger.error(f"fetch_filings: download failed: {e}")

    if index and saved:
        logger.info(f"fetch_filings: indexing {symbol} into the research corpus "
                    "(embeds every page — this can take a few minutes)")
        ingest_documents(symbol)
    return saved


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        sys.exit(1)
    fetch_annual_reports(
        args[0],
        all_years="--all" in args,
        index="--no-index" not in args,
    )
