"""Read-side queries over the persisted corporate-events calendar."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.db.models import CorporateEvent
from backend.schemas.events import CorporateEventRow


class EventsService:
    def list(self, session: Session, window: str = "upcoming", event_type: str | None = None,
             symbol: str | None = None, days: int = 30, limit: int = 200) -> list[CorporateEventRow]:
        """Corporate events in a window.

        window="upcoming" → today onward, soonest first; "recent" → the last
        `days`, newest first; "all" → both, soonest first.
        """
        today = date.today()
        q = session.query(CorporateEvent)
        if event_type:
            q = q.filter(CorporateEvent.event_type == event_type)
        if symbol:
            q = q.filter(CorporateEvent.symbol == symbol.upper())

        if window == "recent":
            q = q.filter(CorporateEvent.event_date < today,
                         CorporateEvent.event_date >= today - timedelta(days=days))
            q = q.order_by(CorporateEvent.event_date.desc())
        elif window == "all":
            q = q.filter(CorporateEvent.event_date >= today - timedelta(days=days))
            q = q.order_by(CorporateEvent.event_date.asc())
        else:  # upcoming
            q = q.filter(CorporateEvent.event_date >= today,
                         CorporateEvent.event_date <= today + timedelta(days=days))
            q = q.order_by(CorporateEvent.event_date.asc())

        return [
            CorporateEventRow(
                symbol=r.symbol, name=r.name, event_type=r.event_type,
                event_date=r.event_date, detail=r.detail, source=r.source,
            )
            for r in q.limit(limit).all()
        ]


events_service = EventsService()
