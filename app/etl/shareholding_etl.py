"""ETL: persist quarterly shareholding snapshots per company.

Two modes:
  * summary (default) — NSE's fast summary pattern → promoter/public %.
  * --detail          — NSE's XBRL filing (app.market.nse_shp) → also FII/DII %.

Upserts the latest few quarters into `shareholdings`, powering promoter/FII/DII
trends and the market-wide "who's accumulating / reducing" view. None-preserving
(detail fills FII/DII without clobbering promoter, and vice-versa). Resumable,
rate-limited, Indian-IP only.

    python -m app.etl.shareholding_etl [--detail] [--limit N] [--sleep S] [--symbols A,B]
"""

import time
from datetime import datetime

from app.db.database import get_session
from app.db.models import Company, Shareholding
from app.utils.logger import logger


def _parse_date(label: str):
    try:
        return datetime.strptime((label or "").title(), "%d-%b-%Y").date()
    except Exception:
        return None


def _from_summary(symbol):
    """[{period_date, period, promoter, public}] from the fast summary API."""
    from backend.services.nse_service import nse_service

    out = []
    for p in nse_service.shareholding(symbol, limit=4):
        pd = _parse_date(p.date)
        if not pd:
            continue
        promoter = public = None
        for h in p.holdings:
            c = (h.category or "").lower()
            if "promoter" in c:
                promoter = h.pct
            elif "public" in c:
                public = h.pct
        out.append({"period_date": pd, "period": p.date, "promoter": promoter, "public": public})
    return out


def _upsert(session, cid, d):
    row = session.query(Shareholding).filter_by(company_id=cid, period_date=d["period_date"]).first()
    if row is None:
        row = Shareholding(company_id=cid, period=d["period"], period_date=d["period_date"])
        session.add(row)
    for col in ("promoter", "public", "fii", "dii", "mf", "insurance", "banks", "pension"):
        v = d.get(col)
        if v is not None:  # None-preserving: don't clobber an existing value
            setattr(row, f"{col}_pct", v)


def run(limit=None, sleep=0.5, symbols=None, detail=False):
    with get_session() as s:
        q = s.query(Company.id, Company.symbol).order_by(Company.id)
        if symbols:
            q = q.filter(Company.symbol.in_(symbols))
        if limit:
            q = q.limit(limit)
        companies = list(q.all())

    if detail and not symbols:
        # resume: skip companies already enriched with the sub-category split
        # (mf_pct) so a re-run only processes the remaining tail. mf_pct is the
        # marker for the deeper/sub-category pass (fii_pct alone = older shallow run).
        with get_session() as s:
            done = {cid for (cid,) in s.query(Shareholding.company_id)
                    .filter(Shareholding.mf_pct.isnot(None)).distinct()}
        before = len(companies)
        companies = [(cid, sym) for cid, sym in companies if cid not in done]
        logger.info("shareholding_etl: resume — skipping %d already-detailed companies", before - len(companies))

    mode = "detail (FII/DII)" if detail else "summary"
    logger.info("shareholding_etl [%s]: %d companies", mode, len(companies))
    rows = miss = 0
    for i, (cid, symbol) in enumerate(companies, 1):
        try:
            if detail:
                from app.market import nse_shp
                recs = nse_shp.detail(symbol, periods=8)
            else:
                recs = _from_summary(symbol)
        except Exception as e:
            logger.debug("shareholding_etl: %s failed: %s", symbol, e)
            recs = []
        if not recs:
            miss += 1
            time.sleep(sleep)
            continue
        try:
            with get_session() as s:
                for d in recs:
                    _upsert(s, cid, d)
                    rows += 1
        except Exception as e:  # one bad company must not kill the whole run
            logger.warning("shareholding_etl: upsert failed for %s: %s", symbol, e)
        if i % 25 == 0:
            logger.info("shareholding_etl: %d/%d (rows=%d, miss=%d)", i, len(companies), rows, miss)
        time.sleep(sleep)

    logger.info("shareholding_etl [%s]: done — rows=%d, miss=%d", mode, rows, miss)
    return rows


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Persist quarterly shareholding snapshots from NSE")
    ap.add_argument("--detail", action="store_true", help="also fetch FII/DII from the XBRL filing")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--symbols", type=str, default=None, help="comma-separated subset")
    a = ap.parse_args()
    syms = [x.strip().upper() for x in a.symbols.split(",")] if a.symbols else None
    run(limit=a.limit, sleep=a.sleep, symbols=syms, detail=a.detail)
