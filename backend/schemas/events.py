"""Schema for the corporate-events calendar endpoints."""

from datetime import date

from backend.schemas.common import APIModel


class CorporateEventRow(APIModel):
    symbol: str
    name: str | None = None
    event_type: str                      # result|dividend|split|bonus|agm|…
    event_date: date
    detail: str | None = None
    source: str | None = None            # "calendar" | "action"
