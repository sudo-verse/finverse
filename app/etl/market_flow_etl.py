"""ETL: daily market-wide FII/DII cash-market provisional flows (₹ crore).

NSE's `fiidiiTradeReact` returns the latest trading day's FII/FPI and DII
buy/sell/net values for the cash segment. It only exposes the most recent day,
so this runs daily (post-close) to build the history. Idempotent per date.
Indian-IP only (NSE blocks foreign IPs) — runs from the Mumbai box.

    python -m app.etl.market_flow_etl
"""

from datetime import datetime

from app.db.database import get_session
from app.db.models import MarketFlow
from app.utils.logger import logger

_URL = "https://www.nseindia.com/api/fiidiiTradeReact"


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _parse_date(s: str):
    try:
        return datetime.strptime((s or "").title(), "%d-%b-%Y").date()
    except Exception:
        return None


def _fetch() -> list:
    """Fetch the provisional FII/DII rows, re-warming the NSE session on a miss."""
    from app.market import nse_shp

    for attempt in (1, 2):
        try:
            r = nse_shp._sess().get(_URL, timeout=15)
            if r.status_code == 200:
                return r.json() or []
            if attempt == 1:
                nse_shp._sess().get(nse_shp._HOME, timeout=10)  # refresh cookies
        except Exception as e:
            logger.debug("market_flow_etl: fetch failed: %s", e)
            if attempt == 1:
                try:
                    nse_shp._sess().get(nse_shp._HOME, timeout=10)
                except Exception:
                    pass
    return []


def run() -> int:
    """Upsert the latest FII/DII flow snapshot. Returns days written."""
    by_date: dict = {}
    for row in _fetch():
        d = _parse_date(row.get("date"))
        if not d:
            continue
        cat = (row.get("category") or "").upper()
        prefix = "fii" if ("FII" in cat or "FPI" in cat) else "dii" if "DII" in cat else None
        if not prefix:
            continue
        rec = by_date.setdefault(d, {})
        rec[f"{prefix}_buy"] = _num(row.get("buyValue"))
        rec[f"{prefix}_sell"] = _num(row.get("sellValue"))
        rec[f"{prefix}_net"] = _num(row.get("netValue"))

    written = 0
    for d, rec in by_date.items():
        with get_session() as s:
            obj = s.query(MarketFlow).filter_by(date=d).first()
            if obj is None:
                obj = MarketFlow(date=d)
                s.add(obj)
            for k, v in rec.items():
                if v is not None:
                    setattr(obj, k, v)
            obj.fetched_at = datetime.utcnow()
            written += 1

    logger.info("market_flow_etl: upserted %d day(s) %s", written, sorted(by_date))
    return written


if __name__ == "__main__":
    run()
