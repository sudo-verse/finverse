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


class ChatRequest(APIModel):
    message: str = Field(min_length=1, max_length=4000)
    symbol: str | None = None  # optionally scope retrieval to one company
    k: int = Field(default=4, ge=1, le=10)


class ChatSource(APIModel):
    source: str
    snippet: str


class ChatOut(APIModel):
    id: str
    role: str = "assistant"
    content: str
    sources: list[ChatSource]
    timestamp: datetime
