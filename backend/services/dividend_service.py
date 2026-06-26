"""Dividend analytics from the corporate-events calendar.

Dividend announcements live in `corporate_events` (event_type="dividend"); the
per-share amount is embedded in the detail text ("Dividend - Rs 3.50 Per
Share"). We parse it and divide by the latest price for an indicative yield.
Amount/yield are shown only where the filing states a figure (many "to consider
dividend" notices carry none).
"""

import re
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.db.models import CorporateEvent
from backend.schemas.dividend import DividendRow
from backend.services import screener_service, universe_service

_AMT_RE = re.compile(r"(?:rs\.?|re\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:/-)?\s*per\s*share", re.I)


def _amount(detail: str | None) -> float | None:
    if not detail:
        return None
    m = _AMT_RE.search(detail)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def feed(session: Session, window: str = "recent", days: int = 60, limit: int = 100,
         universe: str | None = None) -> list[DividendRow]:
    today = date.today()
    q = session.query(CorporateEvent).filter(CorporateEvent.event_type == "dividend")
    if window == "upcoming":
        q = q.filter(CorporateEvent.event_date >= today).order_by(CorporateEvent.event_date.asc())
    else:
        q = q.filter(CorporateEvent.event_date < today,
                     CorporateEvent.event_date >= today - timedelta(days=days)) \
             .order_by(CorporateEvent.event_date.desc())
    events = q.limit(limit * 2).all()

    prices = {r.symbol: r.price for r in screener_service.screen(session)}
    rows: list[DividendRow] = []
    for e in events:
        amt = _amount(e.detail)
        price = prices.get(e.symbol)
        yld = round(amt / price * 100, 2) if (amt and price) else None
        rows.append(DividendRow(
            symbol=e.symbol, name=e.name, amount=amt, yield_pct=yld,
            event_date=e.event_date, detail=e.detail, upcoming=(e.event_date >= today),
        ))
    rows = universe_service.filter_rows(rows, universe)
    return rows[:limit]
