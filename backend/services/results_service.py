"""Earnings/results calendar — result-announcement dates enriched with the
company's latest fundamental trend.

Result dates come from the persisted corporate-events calendar (event_type=
"result"). We have no analyst estimates, so instead of a vs-estimate beat/miss
we attach the latest annual PAT/revenue YoY and momentum (from earnings_service)
as a trend tag — honest context heading into / coming out of results.
"""

from sqlalchemy.orm import Session

from backend.schemas.results_calendar import ResultRow
from backend.services import earnings_service, universe_service
from backend.services.events_service import events_service


def _tag(pat_yoy: float | None, momentum: str | None) -> str | None:
    if pat_yoy is None:
        return None
    if pat_yoy >= 0.15 and momentum == "accelerating":
        return "Strong"
    if pat_yoy >= 0:
        return "Positive"
    if pat_yoy <= -0.20:
        return "Weak"
    return "Soft"


def calendar(session: Session, window: str = "upcoming", days: int = 45,
             limit: int = 200, universe: str | None = None) -> list[ResultRow]:
    events = events_service.list(session, window=window, event_type="result",
                                 days=days, limit=limit * 2)
    earn = {e.symbol: e for e in earnings_service._all(session)}

    rows: list[ResultRow] = []
    for ev in events:
        e = earn.get(ev.symbol)
        rows.append(ResultRow(
            symbol=ev.symbol, name=ev.name, event_date=ev.event_date, detail=ev.detail,
            fy=e.fy if e else None,
            pat_yoy=e.pat_yoy if e else None,
            revenue_yoy=e.revenue_yoy if e else None,
            momentum=e.momentum if e else None,
            tag=_tag(e.pat_yoy, e.momentum) if e else None,
        ))
    return universe_service.filter_rows(rows, universe)[:limit]
