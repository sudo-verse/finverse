"""ETL: daily bulk & block deals from NSE's large-deal snapshot.

`snapshot-capital-market-largedeal` returns the current day's BULK_DEALS_DATA
and BLOCK_DEALS_DATA (named client, side, qty, weighted-avg price). Like the
FII/DII flows it only exposes the latest session, so this runs daily to build
history. Idempotent on the natural key (date,type,symbol,client,side,qty).
Indian-IP only (NSE blocks foreign IPs) — runs from the Mumbai box.

    python -m app.etl.deals_etl
"""

from datetime import datetime

from app.db.database import get_session
from app.db.models import Deal
from app.utils.logger import logger

_URL = "https://www.nseindia.com/api/snapshot-capital-market-largedeal"


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


def _fetch() -> dict:
    from app.market import nse_shp

    for attempt in (1, 2):
        try:
            r = nse_shp._sess().get(_URL, timeout=20)
            if r.status_code == 200:
                return r.json() or {}
            if attempt == 1:
                nse_shp._sess().get(nse_shp._HOME, timeout=10)
        except Exception as e:
            logger.debug("deals_etl: fetch failed: %s", e)
            if attempt == 1:
                try:
                    nse_shp._sess().get(nse_shp._HOME, timeout=10)
                except Exception:
                    pass
    return {}


def _rows(payload: dict, key: str, deal_type: str) -> list[dict]:
    out = []
    for d in payload.get(key, []) or []:
        date = _parse_date(d.get("date"))
        symbol = (d.get("symbol") or "").strip().upper()
        if not date or not symbol:
            continue
        qty = _num(d.get("qty"))
        price = _num(d.get("watp"))
        out.append({
            "deal_date": date, "deal_type": deal_type, "symbol": symbol,
            "name": (d.get("name") or "").strip()[:255],
            "client_name": (d.get("clientName") or "").strip()[:255],
            "side": (d.get("buySell") or "").strip().upper()[:4],
            "quantity": int(qty) if qty is not None else None,
            "price": price,
            "value": round(qty * price, 2) if (qty is not None and price is not None) else None,
            "remarks": (d.get("remarks") or "").strip()[:255] or None,
        })
    return out


def run() -> int:
    """Upsert today's bulk + block deals. Returns rows written."""
    payload = _fetch()
    deals = _rows(payload, "BULK_DEALS_DATA", "bulk") + _rows(payload, "BLOCK_DEALS_DATA", "block")
    written = 0
    for d in deals:
        try:
            with get_session() as s:
                exists = s.query(Deal.id).filter_by(
                    deal_date=d["deal_date"], deal_type=d["deal_type"], symbol=d["symbol"],
                    client_name=d["client_name"], side=d["side"], quantity=d["quantity"],
                ).first()
                if exists:
                    continue
                s.add(Deal(**d))
                written += 1
        except Exception as e:  # one bad row must not kill the run
            logger.debug("deals_etl: upsert failed for %s: %s", d.get("symbol"), e)

    logger.info("deals_etl: %d new deals (bulk+block) for %s", written, payload.get("as_on_date"))
    return written


if __name__ == "__main__":
    run()
