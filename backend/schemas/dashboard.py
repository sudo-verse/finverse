from datetime import date, datetime

from backend.schemas.common import APIModel
from backend.schemas.signal import SignalOut


class DashboardMetrics(APIModel):
    total_companies: int
    total_signals: int
    buy_signals: int
    sell_signals: int
    hold_signals: int
    price_rows: int
    portfolio_value: float | None = None
    portfolio_day_change_pct: float | None = None


class DistributionItem(APIModel):
    name: str
    value: int


class IndustryCount(APIModel):
    industry: str
    count: int


class TrendPoint(APIModel):
    date: date
    buy: int
    sell: int
    hold: int


class NewsEventOut(APIModel):
    id: int
    symbol: str | None = None
    headline: str | None = None
    source: str | None = None
    sentiment: str | None = None
    timestamp: datetime | None = None


class DashboardOut(APIModel):
    metrics: DashboardMetrics
    signal_distribution: list[DistributionItem]
    industry_distribution: list[IndustryCount]
    daily_signal_trend: list[TrendPoint]
    recent_signals: list[SignalOut]
    recent_news: list[NewsEventOut]
