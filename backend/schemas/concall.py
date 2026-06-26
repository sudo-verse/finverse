"""Schemas for concall (earnings-call) transcripts + AI summaries."""

from backend.schemas.common import APIModel


class ConcallRow(APIModel):
    date: str | None = None
    title: str | None = None
    url: str | None = None


class ConcallSummary(APIModel):
    symbol: str
    url: str | None = None
    highlights: list[str] = []
    guidance: str | None = None
    outlook: str | None = None
    risks: list[str] = []
    model: str | None = None
    generated_at: str | None = None
    cached: bool = False
