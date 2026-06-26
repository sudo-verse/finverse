from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.nse import (
    AnnouncementOut,
    AnnualReportOut,
    BrsrOut,
    CompanyProfile,
    CorpActionOut,
    CorpEventOut,
    IntradaySeries,
    LiveQuote,
    PerformanceRow,
    QuarterlyResultOut,
    ShareholdingPeriod,
)
from backend.schemas.conviction import ConvictionRow
from backend.schemas.technicals import TechnicalsOut
from backend.schemas.red_flags import RedFlagsOut
from backend.schemas.earnings import StockEarnings
from backend.schemas.insider import InsiderTrade
from backend.schemas.peers import PeerComparison
from backend.schemas.valuation import ValuationOut
from backend.schemas.radar import StockRange
from backend.schemas.scorecard import ScorecardOut
from backend.schemas.stock import CompanyOut, StockDetailOut
from backend.services import (
    conviction_service,
    earnings_service,
    insider_service,
    red_flags_service,
    technical_service,
    valuation_service,
)
from backend.services.nse_service import nse_service
from backend.services.peer_service import peer_service
from backend.services.radar_service import radar_service
from backend.services.scorecard_service import scorecard_service
from backend.services.stock_service import stock_service

router = APIRouter(tags=["stocks"])

SymbolPath = Path(min_length=1, max_length=32, description="NSE symbol, e.g. RELIANCE")


@router.get("/stocks", response_model=list[CompanyOut], summary="List companies")
def list_stocks(
    db: Session = Depends(get_db),
    search: str | None = Query(None, description="Filter by symbol or name"),
    limit: int = Query(5000, ge=1, le=5000),
) -> list[CompanyOut]:
    """The company master (NIFTY 500 universe loaded by the ETL)."""
    return stock_service.list_companies(db, search=search, limit=limit)


@router.get("/stocks/{symbol}", response_model=StockDetailOut, summary="Full stock analysis")
def get_stock(
    db: Session = Depends(get_db),
    symbol: str = SymbolPath,
    history_days: int = Query(365, ge=30, le=2000, alias="historyDays"),
) -> StockDetailOut:
    """Company details, OHLCV history with SMA 20/50/200 overlays, the full
    quant bundle (returns, volatility, Sharpe, drawdown, trend), financial
    ratios and the stock's recent signals."""
    return stock_service.get_stock_detail(db, symbol, history_days=history_days)


@router.get("/stocks/{symbol}/scorecard", response_model=ScorecardOut,
            summary="Composite stock scorecard")
def get_scorecard(db: Session = Depends(get_db), symbol: str = SymbolPath) -> ScorecardOut:
    """A glanceable multi-factor verdict (valuation, growth, profitability,
    financial health, red flags, momentum) computed from the stock's financials,
    prices and sentiment — each with a good/average/bad call and a one-line why."""
    return scorecard_service.compute(db, symbol)


@router.get("/stocks/{symbol}/peers", response_model=PeerComparison,
            summary="Sector/industry peer comparison")
def get_peers(db: Session = Depends(get_db), symbol: str = SymbolPath,
              limit: int = Query(8, ge=2, le=20)) -> PeerComparison:
    """The stock ranked against its industry (or sector, if the industry group
    is thin) peers on valuation, returns and growth — reuses the screener's
    computed ratios so the same data caveats apply."""
    return peer_service.peers(db, symbol, limit=limit)


@router.get("/stocks/{symbol}/range-52w", response_model=StockRange,
            summary="Position in the 52-week range")
def get_range_52w(db: Session = Depends(get_db), symbol: str = SymbolPath) -> StockRange:
    """Where the stock sits between its 52-week low and high, with % from each
    extreme — for the stock-page range bar."""
    return radar_service.stock_range(db, symbol)


@router.get("/stocks/{symbol}/earnings", response_model=StockEarnings,
            summary="Annual earnings-growth history")
def get_earnings(db: Session = Depends(get_db), symbol: str = SymbolPath) -> StockEarnings:
    """Year-by-year revenue, PAT, EPS and net margin with YoY growth, plus a
    momentum verdict (accelerating/decelerating) — for the stock-page panel."""
    result = earnings_service.stock_earnings(db, symbol)
    return result or StockEarnings(symbol=symbol.upper(), name="")


@router.get("/stocks/{symbol}/insider", response_model=list[InsiderTrade],
            summary="Insider (SEBI PIT) trades")
def get_insider(symbol: str = SymbolPath, limit: int = Query(25, ge=1, le=100)) -> list[InsiderTrade]:
    """Named-insider trades (promoters/directors/KMP buying or selling) from
    SEBI PIT disclosures — live from NSE, per company."""
    return insider_service.stock_insider(symbol.upper(), limit=limit)


@router.get("/stocks/{symbol}/valuation", response_model=ValuationOut,
            summary="Relative fair-value estimate")
def get_valuation(db: Session = Depends(get_db), symbol: str = SymbolPath) -> ValuationOut:
    """Sector-relative, quality-adjusted fair value (P/E×growth + P/B×ROE) with
    upside, margin of safety and a confidence flag — a screening signal, not a
    price target."""
    result = valuation_service.stock(db, symbol)
    return result or ValuationOut(symbol=symbol.upper(), name="")


@router.get("/stocks/{symbol}/conviction", response_model=ConvictionRow | None,
            summary="Composite conviction score")
def get_conviction(db: Session = Depends(get_db), symbol: str = SymbolPath) -> ConvictionRow | None:
    """The stock's 0-100 conviction score with the full per-pillar breakdown
    (valuation, momentum, smart money, insider/SAST, 52-week trend, sentiment).
    Returns null when too few pillars have data to score it."""
    return conviction_service.stock(db, symbol)


@router.get("/stocks/{symbol}/technicals", response_model=TechnicalsOut | None,
            summary="Technical indicators")
def get_technicals(db: Session = Depends(get_db), symbol: str = SymbolPath) -> TechnicalsOut | None:
    """Full technical read from our daily OHLCV — moving averages (20/50/200),
    RSI, MACD, classic pivots, 52-week position and volume — with a composite
    0-100 score and signal flags. A trading-signal view, not advice."""
    return technical_service.technicals(db, symbol)


@router.get("/stocks/{symbol}/red-flags", response_model=RedFlagsOut,
            summary="Red flags (surveillance, pledge, leverage)")
def get_red_flags(db: Session = Depends(get_db), symbol: str = SymbolPath) -> RedFlagsOut:
    """NSE surveillance (ASM/GSM), promoter share pledging and a leverage-based
    financial-stress read for the stock, with a prioritised flag list."""
    return red_flags_service.stock_red_flags(db, symbol)


# ----------------------------------------------------------------------------
# Live NSE data (NextApi GetQuoteApi) — see backend/services/nse_service.py
# ----------------------------------------------------------------------------

@router.get("/stocks/{symbol}/live", response_model=LiveQuote, summary="Live NSE quote")
def get_live_quote(symbol: str = SymbolPath) -> LiveQuote:
    """Real-time price, day range, VWAP, traded volume/value and market cap
    straight from NSE (cached ~30s server-side)."""
    return nse_service.live_quote(symbol.upper())


@router.get(
    "/stocks/{symbol}/announcements",
    response_model=list[AnnouncementOut],
    summary="Corporate announcements",
)
def get_announcements(
    symbol: str = SymbolPath, limit: int = Query(10, ge=1, le=50)
) -> list[AnnouncementOut]:
    """Latest exchange filings/announcements for the company."""
    return nse_service.announcements(symbol.upper(), limit=limit)


@router.get(
    "/stocks/{symbol}/corporate-actions",
    response_model=list[CorpActionOut],
    summary="Corporate actions",
)
def get_corporate_actions(
    symbol: str = SymbolPath, limit: int = Query(10, ge=1, le=50)
) -> list[CorpActionOut]:
    """Dividends, splits, bonuses with ex/record dates."""
    return nse_service.corporate_actions(symbol.upper(), limit=limit)


@router.get(
    "/stocks/{symbol}/annual-reports",
    response_model=list[AnnualReportOut],
    summary="Annual reports",
)
def get_annual_reports(
    symbol: str = SymbolPath, limit: int = Query(10, ge=1, le=50)
) -> list[AnnualReportOut]:
    """Annual report PDFs filed with the exchange (links to NSE archives)."""
    return nse_service.annual_reports(symbol.upper(), limit=limit)


@router.get(
    "/stocks/{symbol}/events",
    response_model=list[CorpEventOut],
    summary="Event calendar",
)
def get_events(symbol: str = SymbolPath, limit: int = Query(5, ge=1, le=20)) -> list[CorpEventOut]:
    """Upcoming corporate events (results, dividends, AGMs)."""
    return nse_service.events(symbol.upper(), limit=limit)


@router.get(
    "/stocks/{symbol}/board-meetings",
    response_model=list[CorpEventOut],
    summary="Board meetings",
)
def get_board_meetings(
    symbol: str = SymbolPath, limit: int = Query(10, ge=1, le=50)
) -> list[CorpEventOut]:
    """Board meeting intimations with purpose and attachments."""
    return nse_service.board_meetings(symbol.upper(), limit=limit)


@router.get(
    "/stocks/{symbol}/results",
    response_model=list[QuarterlyResultOut],
    summary="Reported financial results",
)
def get_results(symbol: str = SymbolPath) -> list[QuarterlyResultOut]:
    """Reported quarterly/annual results (income, PBT, PAT, EPS — ₹ Lakhs)."""
    return nse_service.quarterly_results(symbol.upper())


@router.get("/stocks/{symbol}/intraday", response_model=IntradaySeries, summary="Intraday chart")
def get_intraday(
    symbol: str = SymbolPath,
    days: str = Query("1D", description='Chart window, e.g. "1D"'),
) -> IntradaySeries:
    """Live intraday tick series from NSE's chart API."""
    return nse_service.intraday(symbol.upper(), days=days)


@router.get(
    "/stocks/{symbol}/shareholding",
    response_model=list[ShareholdingPeriod],
    summary="Shareholding pattern",
)
def get_shareholding(
    symbol: str = SymbolPath, limit: int = Query(5, ge=1, le=20)
) -> list[ShareholdingPeriod]:
    """Quarterly shareholding disclosures (promoter / public / FII / DII…)."""
    return nse_service.shareholding(symbol.upper(), limit=limit)


@router.get(
    "/stocks/{symbol}/performance",
    response_model=list[PerformanceRow],
    summary="Returns vs index",
)
def get_performance(symbol: str = SymbolPath) -> list[PerformanceRow]:
    """% price change over standard windows (1W…5Y), stock vs its index."""
    return nse_service.performance(symbol.upper())


@router.get("/stocks/{symbol}/profile", response_model=CompanyProfile, summary="Company profile")
def get_profile(symbol: str = SymbolPath) -> CompanyProfile:
    """Exchange metadata: ISIN, active series, F&O/SLB eligibility, listing
    status, index memberships and the company description when available."""
    return nse_service.profile(symbol.upper())


@router.get("/stocks/{symbol}/brsr", response_model=list[BrsrOut], summary="BRSR reports")
def get_brsr(symbol: str = SymbolPath) -> list[BrsrOut]:
    """Business Responsibility & Sustainability Reports (PDF links)."""
    return nse_service.brsr(symbol.upper())


# ------------------------------ Company terminal ------------------------------

from backend.schemas.stock import CagrRow, PricePoint, ProsConsOut, RatioPoint, StatementRow  # noqa: E402
from backend.services.fundamentals_service import fundamentals_service  # noqa: E402


@router.get("/stocks/{symbol}/history", response_model=list[PricePoint],
            summary="Price history for a range (1M…10Y/MAX)")
def stock_history(
    db: Session = Depends(get_db),
    symbol: str = SymbolPath,
    range: str = Query("1Y", description="1M | 6M | 1Y | 3Y | 5Y | 10Y | MAX"),
) -> list[PricePoint]:
    """Daily close/volume with SMA 20/50/200. Ranges beyond the DB's 1-year
    window are fetched from Yahoo Finance on demand (cached server-side)."""
    return fundamentals_service.history(db, symbol.upper(), range)


@router.get("/stocks/{symbol}/statements", response_model=list[StatementRow],
            summary="Annual financial statements with YoY growth")
def stock_statements(db: Session = Depends(get_db), symbol: str = SymbolPath) -> list[StatementRow]:
    return fundamentals_service.statements(db, symbol.upper())


@router.get("/stocks/{symbol}/ratios", response_model=list[RatioPoint],
            summary="Ratio trends (ROE/ROCE/OPM/NPM/D-E) per fiscal year")
def stock_ratios(db: Session = Depends(get_db), symbol: str = SymbolPath) -> list[RatioPoint]:
    return fundamentals_service.ratios(db, symbol.upper())


@router.get("/stocks/{symbol}/cagr", response_model=list[CagrRow],
            summary="Sales/Profit/EPS/ROE/Price CAGR over 1/3/5/10Y")
def stock_cagr(db: Session = Depends(get_db), symbol: str = SymbolPath) -> list[CagrRow]:
    return fundamentals_service.cagr(db, symbol.upper())


@router.get("/stocks/{symbol}/pros-cons", response_model=ProsConsOut,
            summary="AI-generated pros & cons (cached)")
def stock_pros_cons(
    db: Session = Depends(get_db),
    symbol: str = SymbolPath,
    refresh: bool = Query(False, description="Force regeneration"),
) -> ProsConsOut:
    """Screener-style pros/cons with confidence scores, grounded in Finverse
    metrics/fundamentals/peers/signals (Gemini; cached in company_insights)."""
    return fundamentals_service.pros_cons(db, symbol.upper(), refresh=refresh)
