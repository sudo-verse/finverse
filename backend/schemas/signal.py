from datetime import datetime

from backend.schemas.common import APIModel


class SignalOut(APIModel):
    """One scored news/announcement event from the engine (news_signals)."""

    id: int
    symbol: str | None = None
    company_name: str | None = None
    signal: str  # BUY | SELL | HOLD
    confidence: float | None = None  # engine sentiment_score (0–1)
    sentiment: str | None = None  # positive | negative | neutral
    event_type: str | None = None
    event_title: str | None = None
    source: str | None = None
    price: float | None = None
    published_at: str | None = None  # source-provided time string
    timestamp: datetime | None = None  # ingestion time (created_at)


class SignalFacets(APIModel):
    """Distinct values available for the filter dropdowns."""

    signals: list[str]
    sources: list[str]
    sentiments: list[str]
