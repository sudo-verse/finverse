"""Schemas for the AI Sentiment Intelligence engine (/api/sentiment/*)."""

from backend.schemas.common import APIModel


class Factor(APIModel):
    """One scored indicator/metric with its explanation (explainable AI)."""

    name: str
    value: float | int | None = None
    score: float | None = None      # 0-100
    status: str = "neutral"         # bullish | bearish | neutral | overbought | …
    explanation: str | None = None


class PillarDetail(APIModel):
    name: str                       # Technical | Fundamental | News | Ownership | Market
    score: float | None = None      # 0-100; None = no data (excluded from composite)
    status: str
    summary: str
    factors: list[Factor]


class MomentumRange(APIModel):
    period: str                     # 1W | 2W | 1M | 3M | 6M | 1Y
    low: float
    high: float
    current: float
    change: float                   # fraction over the window


class PivotLevels(APIModel):
    pivot: float
    r1: float
    r2: float
    r3: float
    s1: float
    s2: float
    s3: float


class NewsBucket(APIModel):
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    impact: float | None = None     # -1..1 recency-weighted
    count: int


class NewsItem(APIModel):
    """A recent scored news/announcement headline behind the News pillar."""

    headline: str
    source: str | None = None
    published_at: str | None = None
    sentiment_label: str | None = None   # positive | negative | neutral
    signal: str | None = None            # BUY | SELL | HOLD


class OwnershipRow(APIModel):
    category: str
    pct: float | None = None
    delta: float | None = None      # pp QoQ


class SentimentOut(APIModel):
    symbol: str
    overall: float                  # 0-100
    recommendation: str             # STRONG BUY … STRONG SELL
    confidence: float               # 0-1 (data coverage across pillars)
    pillars: list[PillarDetail]
    reasons: list[str]              # explainable-AI "why"
    risks: list[str]
    momentum: list[MomentumRange]
    pivots: PivotLevels | None = None
    moving_averages: dict[str, float | None]
    news_bucket: NewsBucket
    news_items: list[NewsItem] = []   # recent headlines behind the News pillar
    holdings: list[OwnershipRow]


class LeaderboardEntry(APIModel):
    """One ranked company in the sentiment leaderboard (latest daily snapshot)."""

    rank: int
    symbol: str
    name: str | None = None
    overall: float                  # 0-100
    recommendation: str | None = None
    confidence: float | None = None  # 0-1 data coverage
    technical: float | None = None
    fundamental: float | None = None
    news: float | None = None
    as_of: str                      # snapshot date (YYYY-MM-DD)


class SentimentHistoryPoint(APIModel):
    date: str
    overall: float | None
    technical: float | None
    fundamental: float | None
    news: float | None
    ownership: float | None
    market: float | None
    recommendation: str | None
    reason: str | None = None       # what drove the change vs the prior snapshot
