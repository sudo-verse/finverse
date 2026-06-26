"""Schemas for saved screener filters.

`filters` is the same field→value map the screener UI uses (e.g.
{"pe": "30", "roe": "15"}); the server interprets each field with the shared
kind table (max / min / min-pct) so a saved screen evaluates identically on the
worker (for alerts) and in the browser.
"""

from datetime import datetime

from backend.schemas.common import APIModel


class SavedScreenCreate(APIModel):
    name: str
    filters: dict[str, str] = {}
    industry: str | None = None
    universe: str | None = None
    notify: bool = False


class SavedScreenOut(APIModel):
    id: int
    name: str
    filters: dict[str, str] = {}
    industry: str | None = None
    universe: str | None = None
    notify: bool = False
    last_count: int | None = None
    created_at: datetime | None = None
