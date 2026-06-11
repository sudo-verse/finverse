"""Schemas for the AI Research Copilot (/api/research/*)."""

from datetime import datetime

from pydantic import Field

from backend.schemas.common import APIModel


class ChatTurn(APIModel):
    role: str  # "user" | "assistant"
    content: str = Field(max_length=8000)


class ResearchChatRequest(APIModel):
    symbol: str = Field(min_length=1, max_length=32)
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)
    doc_type: str | None = None   # optional metadata filters
    year: int | None = None
    stream: bool = True


class ResearchCompareRequest(APIModel):
    symbols: list[str] = Field(min_length=2, max_length=3)
    message: str | None = Field(default=None, max_length=4000)
    stream: bool = True


class SourceCitation(APIModel):
    id: str
    label: str               # "Annual Report 2024, page 128"
    source: str              # original filename / signal id
    doc_type: str | None = None
    year: int | None = None
    page: int | None = None
    symbol: str | None = None  # set in compare mode
    snippet: str


class ResearchChatOut(APIModel):
    id: str
    role: str = "assistant"
    content: str
    sources: list[SourceCitation]
    follow_ups: list[str]
    timestamp: datetime


class ResearchCompanyOut(APIModel):
    symbol: str
    name: str
    industry: str | None = None
    indexed_chunks: int = 0      # >0 means filings are in the vector store


class DocTypeSummary(APIModel):
    doc_type: str
    label: str
    documents: int
    chunks: int
    years: list[int]


class CompanySourcesOut(APIModel):
    symbol: str
    name: str
    total_chunks: int
    doc_types: list[DocTypeSummary]
    has_financials: bool         # structured Finverse data availability
    has_price_history: bool
    news_signals: int


class ResearchHistoryItem(APIModel):
    id: int
    symbol: str | None
    mode: str
    question: str
    answer: str | None
    sources: list[SourceCitation]
    created_at: datetime
