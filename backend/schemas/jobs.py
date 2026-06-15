"""Schemas for background jobs (/api/jobs)."""

from backend.schemas.common import APIModel


class IngestJobRequest(APIModel):
    symbol: str | None = None   # None → whole corpus


class JobAccepted(APIModel):
    job_id: str | None = None
    status: str = "queued"
