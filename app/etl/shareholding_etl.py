"""ETL: persist quarterly shareholding snapshots (promoter/public) per company.

Pulls NSE's summary shareholding pattern per symbol and upserts the latest few
quarters into `shareholdings`, so promoter-holding trends and a market-wide
"promoter accumulating / reducing" view can be computed without re-fetching.
FII/DII columns are left null until the detailed-filing source is wired.

Resumable and rate-limited (per-symbol NSE call). Run from an Indian IP.

    python -m app.etl.shareholding_etl [--limit N] [--sleep 0.5] [--symbols A,B]
"""

import time
from datetime import datetime

from app.db.database import get_session
from app.db.models import Company, Shareholding
from app.utils.logger import logger


def _parse_date(label: str):
    try:
        return datetime.strptime(label, "%d-%b-%Y").date()
    except Exception:
        return None


def _extract(holdings):
    promoter = public = None
    for h in holdings:
        c = (h.category or "").lower()
        if "promoter" in c:
            promoter = h.pct
        elif "public" in c:
            public = h.pct
    return promoter, public


def run(limit=None, sleep=0.5, symbols=None):
    from backend.services.nse_service import nse_service

    with get_session() as s:
        q = s.query(Company.id, Company.symbol).order_by(Company.id)
        if symbols:
            q = q.filter(Company.symbol.in_(symbols))
        if limit:
            q = q.limit(limit)
        companies = list(q.all())

    logger.info("shareholding_etl: %d companies", len(companies))
    rows = miss = 0
    for i, (cid, symbol) in enumerate(companies, 1):
        try:
            periods = nse_service.shareholding(symbol, limit=4)
        except Exception as e:
            logger.debug("shareholding_etl: %s failed: %s", symbol, e)
            periods = []
        if not periods:
            miss += 1
            time.sleep(sleep)
            continue
        with get_session() as s:
            for p in periods:
                pd = _parse_date(p.date)
                if not pd:
                    continue
                promoter, public = _extract(p.holdings)
                row = s.query(Shareholding).filter_by(company_id=cid, period_date=pd).first()
                if row:
                    row.promoter_pct, row.public_pct = promoter, public
                else:
                    s.add(Shareholding(company_id=cid, period=p.date, period_date=pd,
                                       promoter_pct=promoter, public_pct=public))
                rows += 1
        if i % 50 == 0:
            logger.info("shareholding_etl: %d/%d (rows=%d, miss=%d)", i, len(companies), rows, miss)
        time.sleep(sleep)

    logger.info("shareholding_etl: done — rows=%d, miss=%d", rows, miss)
    return rows


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Persist quarterly shareholding snapshots from NSE")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--symbols", type=str, default=None, help="comma-separated subset")
    a = ap.parse_args()
    syms = [x.strip().upper() for x in a.symbols.split(",")] if a.symbols else None
    run(limit=a.limit, sleep=a.sleep, symbols=syms)
