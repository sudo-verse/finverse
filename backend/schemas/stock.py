from datetime import date

from backend.schemas.common import APIModel
from backend.schemas.signal import SignalOut


class CompanyOut(APIModel):
    symbol: str
    name: str
    industry: str | None = None
    # The frontend models industry/sector separately; the company master only
    # tracks NSE "industry", so sector mirrors it for now.
    sector: str | None = None
    isin: str | None = None


class PricePoint(APIModel):
    date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    sma20: float | None = None
    sma50: float | None = None
    sma200: float | None = None


class QuantMetrics(APIModel):
    """L4 bundle from app.analytics.metrics.compute_all()."""

    data_points: int
    latest_price: float | None = None
    cumulative_return: float | None = None
    annualized_return: float | None = None
    annualized_volatility: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    trend: str | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None


class Fundamentals(APIModel):
    """L5 ratios from app.analytics.financial_analysis.analyze_symbol()."""

    period: str | None = None
    revenue_growth: float | None = None
    earnings_growth: float | None = None
    net_profit_margin: float | None = None
    roe: float | None = None
    roce: float | None = None
    debt_to_equity: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    eps: float | None = None


class StockDetailOut(APIModel):
    symbol: str
    name: str
    industry: str | None = None
    price: float | None = None
    change: float | None = None
    change_pct: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    week52_high: float | None = None
    week52_low: float | None = None
    recommendation: str  # BUY | SELL | HOLD (latest signal, else trend-derived)
    recommendation_confidence: float | None = None
    quant: QuantMetrics | None = None
    fundamentals: Fundamentals | None = None
    price_history: list[PricePoint]
    recent_signals: list[SignalOut]


# --------------------------- Company terminal ---------------------------

class StatementRow(APIModel):
    """One fiscal year from `financial_statements`, with YoY growth."""

    period: str                       # "FY2024"
    revenue: float | None = None
    net_income: float | None = None
    ebit: float | None = None
    eps: float | None = None
    total_assets: float | None = None
    total_equity: float | None = None
    total_liabilities: float | None = None
    operating_cash_flow: float | None = None
    revenue_growth: float | None = None      # fraction vs prior FY
    net_income_growth: float | None = None
    eps_growth: float | None = None


class RatioPoint(APIModel):
    period: str
    roe: float | None = None          # fractions
    roce: float | None = None
    opm: float | None = None
    npm: float | None = None
    debt_to_equity: float | None = None


class CagrRow(APIModel):
    metric: str                       # "Sales" | "Profit" | "EPS" | "Price" | "ROE"
    y1: float | None = None           # fractions; null when history is short
    y3: float | None = None
    y5: float | None = None
    y10: float | None = None


class ProsConsItem(APIModel):
    point: str
    confidence: float                 # 0..1


class ProsConsOut(APIModel):
    symbol: str
    pros: list[ProsConsItem]
    cons: list[ProsConsItem]
    model: str | None = None
    generated_at: str | None = None
    cached: bool


class SwotOut(APIModel):
    symbol: str
    strengths: list[str] = []
    weaknesses: list[str] = []
    opportunities: list[str] = []
    threats: list[str] = []
    model: str | None = None
    generated_at: str | None = None
    cached: bool = False
