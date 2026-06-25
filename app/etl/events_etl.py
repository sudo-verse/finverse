"""ETL: upcoming/recent corporate events from NSE.

Merges two NSE sources into one calendar:
  * event-calendar     — board meetings (results, dividend intent, fund raising…)
  * corporate-actions  — dividend/split/bonus ex-dates

Each event is classified into a normalized type. Idempotent on
(symbol, date, type). Indian-IP only — runs from the Mumbai box.

    python -m app.etl.events_etl
"""

from datetime import datetime

from app.db.database import get_session
from app.db.models import CorporateEvent
from app.utils.logger import logger

_CAL = "https://www.nseindia.com/api/event-calendar?index=equities"
_CA = "https://www.nseindia.com/api/corporates-corporateActions?index=equities"


def _parse_date(s: str):
    s = (s or "").strip()
    if not s or s == "-":
        return None
    try:
        return datetime.strptime(s.title(), "%d-%b-%Y").date()
    except Exception:
        return None


def _classify(text: str) -> str:
    """Map an NSE purpose/subject string to a normalized event type."""
    t = (text or "").lower()
    if "result" in t:
        return "result"
    if "split" in t or "face value" in t:
        return "split"
    if "bonus" in t:
        return "bonus"
    if "buy back" in t or "buyback" in t or "buy-back" in t:
        return "buyback"
    if "right" in t:
        return "rights"
    if "dividend" in t:
        return "dividend"
    if "annual general" in t or "agm" in t:
        return "agm"
    if "fund rais" in t or "raising of funds" in t or "qip" in t or "preferential" in t:
        return "fundraising"
    return "board_meeting"


def _fetch(url: str):
    from app.market import nse_shp

    for attempt in (1, 2):
        try:
            r = nse_shp._sess().get(url, timeout=20)
            if r.status_code == 200:
                return r.json() or []
            if attempt == 1:
                nse_shp._sess().get(nse_shp._HOME, timeout=10)
        except Exception as e:
            logger.debug("events_etl: fetch %s failed: %s", url, e)
            if attempt == 1:
                try:
                    nse_shp._sess().get(nse_shp._HOME, timeout=10)
                except Exception:
                    pass
    return []


def _collect() -> list[dict]:
    out = []
    for row in _fetch(_CAL):
        sym = (row.get("symbol") or "").strip().upper()
        d = _parse_date(row.get("date"))
        purpose = (row.get("purpose") or "").strip()
        if not sym or not d:
            continue
        detail = purpose
        if row.get("bm_desc"):
            detail = f"{purpose}: {row['bm_desc']}".strip(": ")
        out.append({
            "symbol": sym, "name": (row.get("company") or "").strip()[:255],
            "event_type": _classify(purpose), "event_date": d,
            "detail": detail[:512], "source": "calendar",
        })
    for row in _fetch(_CA):
        sym = (row.get("symbol") or "").strip().upper()
        d = _parse_date(row.get("exDate")) or _parse_date(row.get("recDate"))
        subject = (row.get("subject") or "").strip()
        if not sym or not d:
            continue
        out.append({
            "symbol": sym, "name": (row.get("comp") or "").strip()[:255],
            "event_type": _classify(subject), "event_date": d,
            "detail": subject[:512], "source": "action",
        })
    return out


def run() -> int:
    """Upsert current corporate events. Returns rows written."""
    events = _collect()
    written = 0
    for e in events:
        try:
            with get_session() as s:
                row = s.query(CorporateEvent).filter_by(
                    symbol=e["symbol"], event_date=e["event_date"], event_type=e["event_type"],
                ).first()
                if row is None:
                    row = CorporateEvent(**e, fetched_at=datetime.utcnow())
                    s.add(row)
                    written += 1
                else:  # refresh the detail/name in case the disclosure was revised
                    row.detail, row.name, row.source = e["detail"], e["name"], e["source"]
        except Exception as ex:
            logger.debug("events_etl: upsert failed for %s: %s", e.get("symbol"), ex)

    logger.info("events_etl: %d new events (of %d collected)", written, len(events))
    return written


if __name__ == "__main__":
    run()
