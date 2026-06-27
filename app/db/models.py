from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    """A SaaS account. Per-user data (watchlist, holdings, alerts, …) is scoped
    by user_id; auth is email + bcrypt-hashed password (see backend.core.security)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128))
    plan = Column(String(32), nullable=False, default="free")  # free | pro | …
    is_active = Column(Boolean, nullable=False, default=True)
    stripe_customer_id = Column(String(64), index=True)
    stripe_subscription_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)


class UsageRecord(Base):
    """Per-user, per-day counter for a metered metric (e.g. AI chat, reports).
    Backs plan-based daily quotas. One row per (user, day, metric)."""

    __tablename__ = "usage_records"
    __table_args__ = (UniqueConstraint("user_id", "day", "metric", name="uq_usage_user_day_metric"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    day = Column(Date, nullable=False, index=True)
    metric = Column(String(32), nullable=False)
    count = Column(Integer, nullable=False, default=0)


class ApiKey(Base):
    """A developer API key — lets external callers authenticate to the public
    API as the owning user, with that user's plan limits. We store only a
    SHA-256 hash of the secret; the raw key is shown exactly once at creation."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(64), nullable=False, default="API key")
    # Public, non-secret prefix shown in the UI, e.g. "fv_live_a1b2c3".
    prefix = Column(String(24), nullable=False, index=True)
    last4 = Column(String(4), nullable=False)
    hashed_key = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    revoked_at = Column(DateTime)


class ApiKeyUsage(Base):
    """Per-key, per-day request counter backing API rate limits.
    One row per (api_key, day)."""

    __tablename__ = "api_key_usage"
    __table_args__ = (UniqueConstraint("api_key_id", "day", name="uq_apikey_usage_key_day"),)

    id = Column(Integer, primary_key=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False, index=True)
    day = Column(Date, nullable=False, index=True)
    count = Column(Integer, nullable=False, default=0)


class Company(Base):
    """Company master — one row per listed NSE stock."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(32), unique=True, nullable=False, index=True)  # plain NSE symbol
    name = Column(String(255), nullable=False)
    industry = Column(String(128))   # specific (yfinance "industry"), e.g. "Building Materials"
    sector = Column(String(128))     # broad (yfinance "sector"), e.g. "Basic Materials"
    isin = Column(String(32))
    series = Column(String(8))
    created_at = Column(DateTime, default=datetime.utcnow)

    prices = relationship("PriceHistory", back_populates="company", cascade="all, delete-orphan")
    financials = relationship("FinancialStatement", back_populates="company", cascade="all, delete-orphan")
    signals = relationship("NewsSignal", back_populates="company")


class PriceHistory(Base):
    """Daily OHLCV bars per company."""

    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("company_id", "date", name="uq_price_company_date"),)

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)

    company = relationship("Company", back_populates="prices")


class FinancialStatement(Base):
    """Per-period fundamentals (annual/quarterly). Populated by the L5 ETL;
    schema defined now so analytics can build on it."""

    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint("company_id", "period", "period_type", name="uq_fin_company_period"),
    )

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    period = Column(String(16), nullable=False)        # e.g. "FY2024", "2024-Q1"
    period_type = Column(String(16), nullable=False)   # "annual" | "quarterly"

    revenue = Column(Float)
    net_income = Column(Float)
    ebit = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    current_liabilities = Column(Float)
    total_equity = Column(Float)
    operating_cash_flow = Column(Float)
    eps = Column(Float)
    shares_outstanding = Column(Float)

    company = relationship("Company", back_populates="financials")


class NewsSignal(Base):
    """A scored news/announcement event produced by the engine."""

    __tablename__ = "news_signals"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)  # nullable if unresolved
    ticker = Column(String(32), index=True)
    source = Column(String(64))
    news = Column(String(1024))
    event = Column(String(64))
    sentiment_label = Column(String(16))
    sentiment_score = Column(Float)
    signal = Column(String(16), index=True)
    price = Column(Float)
    published_at = Column(String(64))                 # source-provided time string
    uid = Column(String(255), unique=True, index=True)  # cross-source/run dedup
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="signals")


class AIReport(Base):
    """An AI-generated investment report for a stock (Gemini)."""

    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)
    symbol = Column(String(32), index=True)
    content = Column(Text)
    model = Column(String(64))
    generated_at = Column(DateTime, default=datetime.utcnow)


class WatchlistItem(Base):
    """A stock a user is tracking (unique per user, not globally)."""

    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_watchlist_user_symbol"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(32), nullable=False, index=True)
    note = Column(String(255))
    added_at = Column(DateTime, default=datetime.utcnow)


class AlertRule(Base):
    """User-defined alert condition, evaluated by the background worker.

    kinds: price_above | price_below | sentiment_above | sentiment_below |
           promoter_change | buy_signal
    """

    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(32), nullable=False, index=True)
    kind = Column(String(32), nullable=False)
    threshold = Column(Float)              # price level, score, or pp delta
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered_at = Column(DateTime)   # 24h cooldown anchor


class AlertEvent(Base):
    """A fired alert (also pushed to Telegram). Powers the in-app bell."""

    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), index=True)
    symbol = Column(String(32), index=True)
    message = Column(String(512))
    seen = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SavedScreen(Base):
    """A named, persisted screener filter set per user. The worker re-evaluates
    screens flagged `notify` and fires an AlertEvent when new stocks enter."""

    __tablename__ = "saved_screens"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_savedscreen_user_name"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    filters = Column(JSON, nullable=False)   # {field: rawValue} matching the client filter map
    industry = Column(String(120))
    universe = Column(String(16))
    notify = Column(Boolean, default=False)
    last_symbols = Column(JSON)              # baseline symbol set for alert diffing
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run_at = Column(DateTime)


class SentimentScore(Base):
    """Daily snapshot of the Sentiment Intelligence score per company.
    One row per (symbol, date) — recomputing the same day updates the row."""

    __tablename__ = "sentiment_scores"
    __table_args__ = (UniqueConstraint("symbol", "date", name="uq_sentiment_symbol_date"),)

    id = Column(Integer, primary_key=True)
    symbol = Column(String(32), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    overall = Column(Float)            # 0-100
    technical = Column(Float)
    fundamental = Column(Float)
    news = Column(Float)
    ownership = Column(Float)
    market = Column(Float)
    recommendation = Column(String(16))  # STRONG BUY … STRONG SELL
    confidence = Column(Float)           # 0-1: data coverage across pillars
    created_at = Column(DateTime, default=datetime.utcnow)


class CompanyInsight(Base):
    """Cached AI-derived content per company (pros/cons, insights, …).
    One row per (symbol, kind); regenerating replaces the row."""

    __tablename__ = "company_insights"
    __table_args__ = (UniqueConstraint("symbol", "kind", name="uq_insight_symbol_kind"),)

    id = Column(Integer, primary_key=True)
    symbol = Column(String(32), nullable=False, index=True)
    kind = Column(String(32), nullable=False)      # "pros_cons" | "insights"
    content = Column(Text)                          # JSON payload
    model = Column(String(64))
    generated_at = Column(DateTime, default=datetime.utcnow)


class ResearchChat(Base):
    """One Q&A exchange with the AI Research Copilot (powers chat history)."""

    __tablename__ = "research_chats"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(80), index=True)        # "RELIANCE" or "TCS vs INFY"
    mode = Column(String(16), default="chat")      # "chat" | "compare"
    question = Column(Text, nullable=False)
    answer = Column(Text)
    sources_json = Column(Text)                    # serialized citation list
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PortfolioHolding(Base):
    """A single position in the user's portfolio."""

    __tablename__ = "portfolio_holdings"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_holding_user_symbol"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(32), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    avg_price = Column(Float)  # average buy price (optional, for P&L)
    added_at = Column(DateTime, default=datetime.utcnow)


class MarketFlow(Base):
    """Daily market-wide FII/DII cash-market provisional flow (₹ crore).

    One row per trading day, sourced from NSE's fiidiiTradeReact. Powers the
    "today's institutional flows" dashboard widget + the rolling-net history."""

    __tablename__ = "market_flows"
    __table_args__ = (UniqueConstraint("date", name="uq_market_flow_date"),)

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    fii_buy = Column(Float)
    fii_sell = Column(Float)
    fii_net = Column(Float)
    dii_buy = Column(Float)
    dii_sell = Column(Float)
    dii_net = Column(Float)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class CorporateEvent(Base):
    """An upcoming/recent corporate event — results, dividend, split, bonus, AGM…

    Merges NSE's board-meeting calendar (results & intent) with corporate
    actions (ex-dates for dividend/split/bonus). One row per
    (symbol, date, type). Powers the Events calendar + per-stock event strip."""

    __tablename__ = "corporate_events"
    __table_args__ = (
        UniqueConstraint("symbol", "event_date", "event_type", name="uq_event_natural"),
    )

    id = Column(Integer, primary_key=True)
    symbol = Column(String(32), nullable=False, index=True)
    name = Column(String(255))
    event_type = Column(String(16), nullable=False, index=True)  # result|dividend|split|…
    event_date = Column(Date, nullable=False, index=True)         # ex-date or meeting date
    detail = Column(String(512))                                  # subject/purpose text
    source = Column(String(16))                                   # "calendar" | "action"
    fetched_at = Column(DateTime, default=datetime.utcnow)


class Deal(Base):
    """A bulk or block deal disclosed by NSE (large trade by a named client).

    One row per (date, type, symbol, client, side, qty) — the natural key NSE
    publishes. Sourced from the daily large-deal snapshot; powers the Deals
    feed and the per-stock recent-deals panel."""

    __tablename__ = "deals"
    __table_args__ = (
        UniqueConstraint("deal_date", "deal_type", "symbol", "client_name", "side",
                         "quantity", name="uq_deal_natural"),
    )

    id = Column(Integer, primary_key=True)
    deal_date = Column(Date, nullable=False, index=True)
    deal_type = Column(String(8), nullable=False)      # "bulk" | "block"
    symbol = Column(String(32), nullable=False, index=True)
    name = Column(String(255))
    client_name = Column(String(255))
    side = Column(String(4))                            # "BUY" | "SELL"
    quantity = Column(BigInteger)
    price = Column(Float)                                # weighted-avg trade price
    value = Column(Float)                                # quantity × price (₹)
    remarks = Column(String(255))
    fetched_at = Column(DateTime, default=datetime.utcnow)


class Shareholding(Base):
    """Quarterly shareholding snapshot per company (one row per filing period).

    Promoter/public come from NSE's summary pattern; fii/dii are reserved for
    the detailed-filing parser (left null until that source is wired)."""

    __tablename__ = "shareholdings"
    __table_args__ = (UniqueConstraint("company_id", "period_date", name="uq_shp_company_period"),)

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    period = Column(String(16), nullable=False)        # label, e.g. "31-Mar-2026"
    period_date = Column(Date, nullable=False, index=True)
    promoter_pct = Column(Float)
    public_pct = Column(Float)
    fii_pct = Column(Float)    # foreign institutions (FPI) aggregate
    dii_pct = Column(Float)    # domestic institutions aggregate
    # DII sub-categories (from the detailed XBRL filing), for "who's buying":
    mf_pct = Column(Float)         # Mutual Funds / UTI
    insurance_pct = Column(Float)  # Insurance companies (LIC, …)
    banks_pct = Column(Float)      # Banks
    pension_pct = Column(Float)    # Provident / pension funds
    fetched_at = Column(DateTime, default=datetime.utcnow)
