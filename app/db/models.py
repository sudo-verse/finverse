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
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Company(Base):
    """Company master — one row per listed NSE stock."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(32), unique=True, nullable=False, index=True)  # plain NSE symbol
    name = Column(String(255), nullable=False)
    industry = Column(String(128))
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
    """A stock the user is tracking."""

    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(32), unique=True, nullable=False, index=True)
    note = Column(String(255))
    added_at = Column(DateTime, default=datetime.utcnow)


class AlertRule(Base):
    """User-defined alert condition, evaluated by the background worker.

    kinds: price_above | price_below | sentiment_above | sentiment_below |
           promoter_change | buy_signal
    """

    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True)
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
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), index=True)
    symbol = Column(String(32), index=True)
    message = Column(String(512))
    seen = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


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
    symbol = Column(String(80), index=True)        # "RELIANCE" or "TCS vs INFY"
    mode = Column(String(16), default="chat")      # "chat" | "compare"
    question = Column(Text, nullable=False)
    answer = Column(Text)
    sources_json = Column(Text)                    # serialized citation list
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PortfolioHolding(Base):
    """A single position in the user's portfolio."""

    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(32), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    avg_price = Column(Float)  # average buy price (optional, for P&L)
    added_at = Column(DateTime, default=datetime.utcnow)
