"""ETL: enrich the company master with sector/industry from Yahoo Finance.

NSE's EQUITY_L master has no sector data, so we backfill it per-symbol from
yfinance `.info` — broad ``sector`` (e.g. "Basic Materials") plus specific
``industry`` (e.g. "Building Materials"). One network call per symbol, so the
full ~2,400-stock universe takes a while and Yahoo rate-limits; the job is
therefore **resumable**: companies that already have a ``sector`` are skipped,
and resolved rows are committed in batches as they come in. Re-run it until the
"miss" count stops shrinking; pass ``--redo`` to re-fetch everything.

    python -m app.etl.sector_etl [--limit N] [--sleep 0.4] [--redo]
"""

import time

import yfinance as yf

from app.db.database import get_session
from app.db.models import Company
from app.utils.logger import logger


def _pending(redo: bool = False):
    with get_session() as session:
        q = session.query(Company.id, Company.symbol).order_by(Company.id)
        if not redo:
            q = q.filter(Company.sector.is_(None))
        return list(q.all())


def _flush(updates):
    """updates: list of (company_id, sector, industry)."""
    with get_session() as session:
        for cid, sector, industry in updates:
            c = session.get(Company, cid)
            if not c:
                continue
            if sector:
                c.sector = sector
            if industry:
                c.industry = industry


def run(limit=None, sleep=0.4, redo=False, batch=50):
    pending = _pending(redo=redo)
    if limit:
        pending = pending[:limit]
    logger.info("sector_etl: %d companies to enrich", len(pending))

    resolved = miss = 0
    updates: list[tuple[int, str | None, str | None]] = []
    for i, (cid, symbol) in enumerate(pending, 1):
        sector = industry = None
        try:
            info = yf.Ticker(f"{symbol}.NS").info or {}
            sector = (info.get("sector") or "").strip() or None
            industry = (info.get("industry") or "").strip() or None
        except Exception as e:  # rate limits / delisted / no data — skip, retry next run
            logger.debug("sector_etl: %s failed: %s", symbol, e)

        if sector or industry:
            updates.append((cid, sector, industry))
            resolved += 1
        else:
            miss += 1

        if len(updates) >= batch:
            _flush(updates)
            updates = []
            logger.info("sector_etl: %d/%d (resolved=%d, miss=%d)",
                        i, len(pending), resolved, miss)
        time.sleep(sleep)

    if updates:
        _flush(updates)
    logger.info("sector_etl: done — resolved=%d, miss=%d", resolved, miss)
    return resolved


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Backfill company sector/industry from Yahoo Finance")
    p.add_argument("--limit", type=int, default=None, help="cap number of companies (testing)")
    p.add_argument("--sleep", type=float, default=0.4, help="seconds between symbols")
    p.add_argument("--redo", action="store_true", help="re-fetch all, not just rows missing a sector")
    args = p.parse_args()
    run(limit=args.limit, sleep=args.sleep, redo=args.redo)
