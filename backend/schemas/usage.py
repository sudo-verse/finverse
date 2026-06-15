"""Schemas for plan usage (/api/usage)."""

from backend.schemas.common import APIModel


class UsageMetric(APIModel):
    metric: str
    label: str
    used: int
    limit: int | None = None   # None = unlimited


class UsageOut(APIModel):
    plan: str
    metrics: list[UsageMetric]
