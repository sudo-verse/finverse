"""Signal feed: SQL-level filtering + pagination over `news_signals`.

This is API-layer data access (the Streamlit app filtered a full DataFrame in
memory); the scoring/business logic itself lives in the engine and is not
re-implemented here.
"""

import logging

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Company, NewsSignal
from backend.schemas.common import Paginated
from backend.schemas.signal import SignalFacets, SignalOut

logger = logging.getLogger("finverse.api")

_SIGNAL_COLUMNS = (
    NewsSignal.id,
    NewsSignal.ticker,
    Company.name,
    NewsSignal.signal,
    NewsSignal.sentiment_score,
    NewsSignal.sentiment_label,
    NewsSignal.event,
    NewsSignal.news,
    NewsSignal.source,
    NewsSignal.price,
    NewsSignal.published_at,
    NewsSignal.created_at,
)


def row_to_signal(row) -> SignalOut:
    """Map a (_SIGNAL_COLUMNS) result row onto the response schema."""
    (
        id_, ticker, company_name, signal, score, sentiment,
        event, news, source, price, published_at, created_at,
    ) = row
    return SignalOut(
        id=id_,
        symbol=ticker,
        company_name=company_name,
        signal=signal or "HOLD",
        confidence=score,
        sentiment=sentiment,
        event_type=event,
        event_title=news,
        source=source,
        price=price,
        published_at=published_at,
        timestamp=created_at,
    )


def base_signal_query(session: Session):
    return (
        session.query(*_SIGNAL_COLUMNS)
        .outerjoin(Company, NewsSignal.company_id == Company.id)
    )


class SignalService:
    def list_signals(
        self,
        session: Session,
        *,
        page: int,
        page_size: int,
        signal: str | None = None,
        sentiment: str | None = None,
        source: str | None = None,
        search: str | None = None,
    ) -> Paginated[SignalOut]:
        q = base_signal_query(session)

        if signal:
            q = q.filter(NewsSignal.signal == signal.upper())
        if sentiment:
            q = q.filter(NewsSignal.sentiment_label == sentiment.lower())
        if source:
            q = q.filter(NewsSignal.source == source)
        if search:
            like = f"%{search.strip()}%"
            q = q.filter(
                or_(
                    NewsSignal.ticker.ilike(like),
                    Company.name.ilike(like),
                    NewsSignal.news.ilike(like),
                )
            )

        total = q.count()
        total_pages = max(1, -(-total // page_size))  # ceil
        page = min(page, total_pages)

        rows = (
            q.order_by(NewsSignal.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return Paginated[SignalOut](
            items=[row_to_signal(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def facets(self, session: Session) -> SignalFacets:
        """Distinct filter values for the UI dropdowns."""
        def distinct(col):
            return sorted(
                v for (v,) in session.query(col).distinct().all() if v is not None
            )

        return SignalFacets(
            signals=distinct(NewsSignal.signal),
            sources=distinct(NewsSignal.source),
            sentiments=distinct(NewsSignal.sentiment_label),
        )


signal_service = SignalService()
