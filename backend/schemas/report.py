from datetime import datetime

from pydantic import Field

from backend.schemas.common import APIModel


class ReportRequest(APIModel):
    symbol: str = Field(min_length=1, max_length=32)
    use_cache: bool = True  # False forces regeneration


class ReportOut(APIModel):
    symbol: str
    report_md: str
    model: str | None = None
    generated_at: datetime | None = None
    cached: bool
