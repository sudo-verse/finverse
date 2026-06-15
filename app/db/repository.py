"""Data-access helpers (upserts/lookups) used by the ETL and the engine."""

from app.db.database import engine, get_session
from app.db.models import (
    AIReport,
    Company,
    FinancialStatement,
    NewsSignal,
    PortfolioHolding,
    PriceHistory,
)


def get_company_id_by_symbol(session, symbol):
    if not symbol:
        return None
    company = session.query(Company).filter_by(symbol=symbol).first()
    return company.id if company else None


def upsert_company(session, symbol, name, industry=None, isin=None, series=None):
    company = session.query(Company).filter_by(symbol=symbol).first()
    if company:
        company.name = name or company.name
        company.industry = industry or company.industry
        company.isin = isin or company.isin
        company.series = series or company.series
    else:
        company = Company(
            symbol=symbol, name=name, industry=industry, isin=isin, series=series
        )
        session.add(company)
    return company


def upsert_price(session, company_id, date, open_, high, low, close, volume):
    row = (
        session.query(PriceHistory)
        .filter_by(company_id=company_id, date=date)
        .first()
    )
    if row:
        row.open, row.high, row.low, row.close, row.volume = open_, high, low, close, volume
    else:
        session.add(
            PriceHistory(
                company_id=company_id, date=date,
                open=open_, high=high, low=low, close=close, volume=volume,
            )
        )


def upsert_financial(session, company_id, period, period_type, **fields):
    row = (
        session.query(FinancialStatement)
        .filter_by(company_id=company_id, period=period, period_type=period_type)
        .first()
    )
    if row:
        for k, v in fields.items():
            setattr(row, k, v)
    else:
        session.add(FinancialStatement(
            company_id=company_id, period=period, period_type=period_type, **fields
        ))


def save_signal_to_db(signal_dict):
    """Persist one engine signal. Idempotent on `uid`. Best-effort: returns
    True if written, False if skipped/failed (never raises into the engine)."""
    uid = signal_dict.get("uid")
    try:
        with get_session() as session:
            if uid and session.query(NewsSignal).filter_by(uid=uid).first():
                return False

            company_id = get_company_id_by_symbol(session, signal_dict.get("ticker"))

            session.add(NewsSignal(
                company_id=company_id,
                ticker=signal_dict.get("ticker"),
                source=signal_dict.get("source"),
                news=(signal_dict.get("news") or "")[:1024],
                event=signal_dict.get("event"),
                sentiment_label=signal_dict.get("label"),
                sentiment_score=signal_dict.get("score"),
                signal=signal_dict.get("signal"),
                price=signal_dict.get("price"),
                published_at=signal_dict.get("time"),
                uid=uid,
            ))
        return True
    except Exception:
        # DB persistence must never break the live engine
        return False


def save_report(symbol, content, model):
    """Persist an AI report. Creates the table on first use (SQLite-safe)."""
    AIReport.__table__.create(engine, checkfirst=True)
    with get_session() as session:
        company_id = get_company_id_by_symbol(session, symbol)
        report = AIReport(
            company_id=company_id, symbol=symbol, content=content, model=model
        )
        session.add(report)


def get_latest_report(symbol):
    """Return the most recent report for a symbol, or None."""
    AIReport.__table__.create(engine, checkfirst=True)
    with get_session() as session:
        row = (
            session.query(AIReport)
            .filter_by(symbol=symbol)
            .order_by(AIReport.generated_at.desc())
            .first()
        )
        if not row:
            return None
        return {
            "symbol": row.symbol,
            "content": row.content,
            "model": row.model,
            "generated_at": row.generated_at,
        }


# --- AI Research Copilot chat history ---

def save_research_chat(user_id, symbol, question, answer, sources_json, mode="chat"):
    """Persist one copilot exchange. Best-effort: history must never break chat."""
    from app.db.models import ResearchChat

    try:
        ResearchChat.__table__.create(engine, checkfirst=True)
        with get_session() as session:
            session.add(ResearchChat(
                user_id=user_id, symbol=symbol, mode=mode, question=question,
                answer=answer, sources_json=sources_json,
            ))
        return True
    except Exception:
        return False


def get_research_history(user_id, symbol=None, limit=30):
    from app.db.models import ResearchChat

    ResearchChat.__table__.create(engine, checkfirst=True)
    with get_session() as session:
        q = (session.query(ResearchChat)
             .filter(ResearchChat.user_id == user_id)
             .order_by(ResearchChat.id.desc()))
        if symbol:
            q = q.filter(ResearchChat.symbol == symbol)
        rows = q.limit(limit).all()
        return [
            {
                "id": r.id, "symbol": r.symbol, "mode": r.mode,
                "question": r.question, "answer": r.answer,
                "sources_json": r.sources_json, "created_at": r.created_at,
            }
            for r in rows
        ]


# --- Portfolio holdings ---

def add_holding(user_id, symbol, quantity, avg_price=None):
    """Add or update a holding. If the symbol exists, accumulate quantity and
    blend the average price."""
    PortfolioHolding.__table__.create(engine, checkfirst=True)
    with get_session() as session:
        row = session.query(PortfolioHolding).filter_by(user_id=user_id, symbol=symbol).first()
        if row:
            # weighted-average the buy price across the combined quantity
            if avg_price is not None and row.avg_price is not None:
                total_qty = row.quantity + quantity
                row.avg_price = (
                    (row.avg_price * row.quantity + avg_price * quantity) / total_qty
                    if total_qty else row.avg_price
                )
            elif avg_price is not None:
                row.avg_price = avg_price
            row.quantity += quantity
        else:
            session.add(PortfolioHolding(
                user_id=user_id, symbol=symbol, quantity=quantity, avg_price=avg_price
            ))


def list_holdings(user_id):
    PortfolioHolding.__table__.create(engine, checkfirst=True)
    with get_session() as session:
        rows = (session.query(PortfolioHolding)
                .filter_by(user_id=user_id)
                .order_by(PortfolioHolding.symbol).all())
        return [
            {"symbol": r.symbol, "quantity": r.quantity, "avg_price": r.avg_price}
            for r in rows
        ]


def clear_holdings(user_id):
    PortfolioHolding.__table__.create(engine, checkfirst=True)
    with get_session() as session:
        session.query(PortfolioHolding).filter_by(user_id=user_id).delete()
