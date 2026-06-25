"""Schema for the market-wide corporate-announcements feed."""

from backend.schemas.common import APIModel


class AnnouncementFeedRow(APIModel):
    symbol: str | None = None
    name: str | None = None
    category: str = "other"          # classified bucket (order/rating/result/…)
    desc: str | None = None          # NSE's own label ("Outcome of Board Meeting")
    detail: str | None = None        # attchmntText — the human-readable summary
    broadcast_at: str | None = None  # ISO-ish sortable timestamp
    display_time: str | None = None  # NSE's display string ("26-Jun-2026 00:23:03")
    attachment_url: str | None = None
    industry: str | None = None
    has_xbrl: bool = False
