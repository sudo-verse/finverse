"""L5 — Financial analysis: derive ratios from `financial_statements`.

Covers growth, profitability, leverage and valuation. Valuation ratios use the
latest close from `price_history` when available.
"""

from app.db.database import get_session
from app.db.models import Company, FinancialStatement, PriceHistory


def _safe_div(a, b):
    if a is None or b in (None, 0):
        return None
    return a / b


def _latest_close(session, company_id):
    row = (
        session.query(PriceHistory.close)
        .filter_by(company_id=company_id)
        .order_by(PriceHistory.date.desc())
        .first()
    )
    return float(row[0]) if row and row[0] is not None else None


def analyze_symbol(symbol: str) -> dict:
    with get_session() as session:
        company = session.query(Company).filter_by(symbol=symbol).first()
        if not company:
            return {"symbol": symbol, "error": "unknown symbol"}

        statements = (
            session.query(FinancialStatement)
            .filter_by(company_id=company.id, period_type="annual")
            .order_by(FinancialStatement.period.desc())
            .all()
        )
        if not statements:
            return {"symbol": symbol, "error": "no financial statements"}

        latest = statements[0]
        prev = statements[1] if len(statements) > 1 else None
        price = _latest_close(session, company.id)

        # --- Growth ---
        revenue_growth = (
            _safe_div(latest.revenue - prev.revenue, prev.revenue)
            if prev and latest.revenue is not None and prev.revenue is not None
            else None
        )
        earnings_growth = (
            _safe_div(latest.net_income - prev.net_income, prev.net_income)
            if prev and latest.net_income is not None and prev.net_income is not None
            else None
        )

        # --- Profitability ---
        net_margin = _safe_div(latest.net_income, latest.revenue)
        roe = _safe_div(latest.net_income, latest.total_equity)
        capital_employed = (
            latest.total_assets - latest.current_liabilities
            if latest.total_assets is not None and latest.current_liabilities is not None
            else None
        )
        roce = _safe_div(latest.ebit, capital_employed)

        # --- Leverage ---
        debt_to_equity = _safe_div(latest.total_liabilities, latest.total_equity)

        # --- Valuation ---
        pe = _safe_div(price, latest.eps) if price is not None else None
        bvps = _safe_div(latest.total_equity, latest.shares_outstanding)
        pb = _safe_div(price, bvps) if price is not None else None

        return {
            "symbol": symbol,
            "company": company.name,
            "period": latest.period,
            "latest_price": price,
            # growth
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            # profitability
            "net_profit_margin": net_margin,
            "roe": roe,
            "roce": roce,
            # leverage
            "debt_to_equity": debt_to_equity,
            # valuation
            "pe_ratio": pe,
            "pb_ratio": pb,
            "eps": latest.eps,
        }


def analyze_all(limit=None):
    with get_session() as session:
        q = session.query(Company.symbol).order_by(Company.symbol)
        if limit:
            q = q.limit(limit)
        symbols = [s for (s,) in q.all()]

    results = []
    for sym in symbols:
        r = analyze_symbol(sym)
        if "error" not in r:
            results.append(r)
    return results
