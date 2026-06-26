"""Schemas for watchlist + alerts (/api/watchlist, /api/alerts)."""

from datetime import datetime

from pydantic import Field

from backend.schemas.common import APIModel

ALERT_KINDS = (
    "price_above", "price_below",
    "sentiment_above", "sentiment_below",
    "promoter_change", "buy_signal",
    "near_52w_high", "near_52w_low",
)


class WatchlistCreate(APIModel):
    symbol: str = Field(min_length=1, max_length=32)
    note: str | None = Field(default=None, max_length=255)


class WatchlistItemOut(APIModel):
    symbol: str
    name: str | None = None
    industry: str | None = None
    note: str | None = None
    added_at: datetime
    # live enrichment (best-effort; null when NSE/sentiment data is missing)
    price: float | None = None
    change_pct: float | None = None
    sentiment: float | None = None
    recommendation: str | None = None
    alert_count: int = 0


class AlertRuleCreate(APIModel):
    symbol: str = Field(min_length=1, max_length=32)
    kind: str
    threshold: float | None = None


class AlertRuleOut(APIModel):
    id: int
    symbol: str
    kind: str
    threshold: float | None
    active: bool
    created_at: datetime
    last_triggered_at: datetime | None


class AlertEventOut(APIModel):
    id: int
    symbol: str | None
    message: str | None
    seen: bool
    created_at: datetime
