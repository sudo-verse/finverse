"""Schemas for live NSE data (NextApi GetQuoteApi endpoints).

Date/time fields stay as the strings NSE provides — formats vary by endpoint
("10-Jun-2026 16:23:16", "05-Jun-2026", "Mar-2026") and the UI shows them
verbatim.
"""

from backend.schemas.common import APIModel


class LiveQuote(APIModel):
    """getSymbolData — real-time quote."""

    symbol: str
    company_name: str | None = None
    isin: str | None = None
    last_price: float | None = None
    change: float | None = None
    p_change: float | None = None  # percent, e.g. -0.83
    open: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    previous_close: float | None = None
    average_price: float | None = None  # VWAP
    total_traded_volume: float | None = None
    total_traded_value: float | None = None
    market_cap: float | None = None  # last_price × issued_size
    free_float_market_cap: float | None = None
    issued_size: float | None = None
    face_value: float | None = None
    delivery_to_traded: float | None = None


class AnnouncementOut(APIModel):
    """getCorporateAnnouncement — exchange filings."""

    subject: str | None = None
    details: str | None = None
    attachment_url: str | None = None
    broadcast_at: str | None = None
    industry: str | None = None


class CorpActionOut(APIModel):
    """getCorpAction — dividends, splits, bonuses."""

    subject: str | None = None
    ex_date: str | None = None
    record_date: str | None = None
    series: str | None = None
    face_value: str | None = None


class AnnualReportOut(APIModel):
    """getCorpAnnualReport — annual report PDFs."""

    company_name: str | None = None
    from_year: str | None = None
    to_year: str | None = None
    broadcast_at: str | None = None
    file_url: str | None = None
    file_size: str | None = None


class CorpEventOut(APIModel):
    """getCorpEventCalender / getCorpBoardMeeting — upcoming/past events."""

    date: str | None = None
    purpose: str | None = None
    description: str | None = None
    attachment_url: str | None = None
    announced_at: str | None = None


class QuarterlyResultOut(APIModel):
    """getFinancialStatus — reported results. Monetary values in ₹ Lakhs."""

    period: str | None = None  # e.g. "Mar-2026"
    to_date: str | None = None
    audited: str | None = None
    total_income: float | None = None
    profit_before_tax: float | None = None
    net_profit: float | None = None
    eps: float | None = None
    broadcast_at: str | None = None


class IndexQuote(APIModel):
    """getIndexData — live index quote."""

    name: str
    last: float | None = None
    perc_change: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    previous_close: float | None = None
    year_high: float | None = None
    year_low: float | None = None
    time: str | None = None


class GiftNiftyQuote(APIModel):
    last_price: float | None = None
    day_change: float | None = None
    per_change: float | None = None
    expiry: str | None = None
    time: str | None = None


class UsdInrQuote(APIModel):
    ltp: float | None = None
    updated_time: str | None = None
    expiry: str | None = None


class MarketOverview(APIModel):
    """getIndexData + getGiftNifty + getPreOpenMarketStatus combined."""

    indices: list[IndexQuote]
    gift_nifty: GiftNiftyQuote | None = None
    usd_inr: UsdInrQuote | None = None
    total_market_cap_lac_cr: float | None = None
    market_status: str | None = None  # raw NSE code, e.g. "O", "PO", "PC"


class MoverOut(APIModel):
    """getTopTenStock rows."""

    symbol: str
    last_price: float | None = None
    change: float | None = None
    p_change: float | None = None
    previous_close: float | None = None
    traded_volume: float | None = None
    traded_value: float | None = None


class MarketMovers(APIModel):
    gainers: list[MoverOut]
    losers: list[MoverOut]
    most_active: list[MoverOut]
    timestamp: str | None = None


class IntradayPoint(APIModel):
    time: int  # epoch milliseconds
    price: float


class IntradaySeries(APIModel):
    """getSymbolChartData — intraday tick series."""

    symbol: str
    points: list[IntradayPoint]


class HoldingCategory(APIModel):
    category: str
    pct: float | None = None


class ShareholdingPeriod(APIModel):
    """getShareholdingPattern — one disclosure period."""

    date: str
    holdings: list[HoldingCategory]


class PerformanceRow(APIModel):
    """getYearwiseData — % return over a period, stock vs its index."""

    period: str
    stock: float | None = None  # percent
    index: float | None = None  # percent


class CompanyProfile(APIModel):
    """getMetaData + getIndexList + getRegDetails + about text."""

    symbol: str
    company_name: str | None = None
    isin: str | None = None
    active_series: list[str] = []
    is_fno: bool = False
    is_slb: bool = False
    is_etf: bool = False
    is_suspended: bool = False
    listing_status: str | None = None
    indices: list[str] = []
    about: str | None = None


class BrsrOut(APIModel):
    """getCorpBrsr — Business Responsibility & Sustainability Reports."""

    fy_from: str | None = None
    fy_to: str | None = None
    attachment_url: str | None = None
    file_size: str | None = None
    submitted_at: str | None = None


class QuarterOption(APIModel):
    label: str
    value: str


class MarqueeItem(APIModel):
    """getMarqueData — NIFTY 50 constituent ticker."""

    symbol: str
    last_price: float | None = None
    change: float | None = None
    per_change: float | None = None


class TurnoverRow(APIModel):
    """getMarketTurnoverSummary — one market segment."""

    segment: str | None = None
    instrument: str | None = None
    turnover: float | None = None  # ₹
    trades: float | None = None
    volume: float | None = None
    prev_turnover: float | None = None
    timestamp: str | None = None


class NsePeerOut(APIModel):
    """getPeerComparisonData — live industry peer metrics."""

    symbol: str
    last_price: float | None = None
    p_change: float | None = None
    market_cap: float | None = None  # ₹
    pe: float | None = None
    eps: float | None = None
    net_profit: float | None = None  # ₹ Lakhs (pat)
    total_income: float | None = None  # ₹ Lakhs
    debt_to_equity: float | None = None
    promoter_holding: float | None = None  # percent
    volume: float | None = None
    traded_value: float | None = None
