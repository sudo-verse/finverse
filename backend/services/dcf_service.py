"""DCF / scenario intrinsic-value builder.

A guided discounted-cash-flow model on the financials we already hold. We lack
a clean capex line, so the free-cash-flow proxy is operating cash flow (falling
back to net income) and the model is run as equity FCF discounted at a cost of
equity — i.e. it returns equity value per share directly. Bull/base/bear
scenarios vary growth and discount; the frontend lets the user tweak the
assumptions and recompute live. A screening estimate, not a target.
"""

import math

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Company, FinancialStatement, PriceHistory
from backend.schemas.dcf import DcfOut, DcfScenario

_YEARS = 10
_DISCOUNT = 0.12      # base cost of equity for Indian large/mid caps
_TERMINAL = 0.04


def _latest_price(session: Session, company_id: int) -> float | None:
    row = (
        session.query(PriceHistory.close)
        .filter(PriceHistory.company_id == company_id, PriceHistory.close.isnot(None))
        .order_by(PriceHistory.date.desc())
        .first()
    )
    if row and row.close is not None and not math.isnan(row.close):
        return float(row.close)
    return None


def _cagr(series: list[float]) -> float | None:
    pts = [x for x in series if x is not None and x > 0]
    if len(pts) < 2:
        return None
    yrs = len(pts) - 1
    return (pts[-1] / pts[0]) ** (1 / yrs) - 1


def _intrinsic(fcf: float, growth: float, terminal_growth: float, discount: float,
               years: int, shares: float) -> float | None:
    if shares <= 0 or discount <= terminal_growth:
        return None
    pv = 0.0
    f = fcf
    for t in range(1, years + 1):
        f *= (1 + growth)
        pv += f / (1 + discount) ** t
    terminal = f * (1 + terminal_growth) / (discount - terminal_growth)
    pv += terminal / (1 + discount) ** years
    return pv / shares


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def compute(session: Session, symbol: str) -> DcfOut:
    company = session.query(Company).filter(Company.symbol == symbol.upper()).first()
    if company is None:
        return DcfOut(symbol=symbol.upper(), applicable=False, note="Unknown symbol.")

    fins = (
        session.query(FinancialStatement)
        .filter_by(company_id=company.id, period_type="annual")
        .order_by(FinancialStatement.period)
        .all()
    )
    out = DcfOut(symbol=company.symbol, name=company.name,
                 price=_latest_price(session, company.id))
    if not fins:
        out.applicable = False
        out.note = "No financial statements ingested for this company yet."
        return out

    latest = fins[-1]
    fcf = latest.operating_cash_flow
    out.fcf_source = "operating cash flow"
    if fcf is None or fcf == 0:
        fcf = latest.net_income
        out.fcf_source = "net income"
    out.base_fcf = fcf
    out.shares = latest.shares_outstanding

    if not fcf or fcf <= 0 or not latest.shares_outstanding:
        out.applicable = False
        out.note = "Latest free cash flow is negative or zero, or shares are unknown — a DCF isn't meaningful here."
        return out

    hist = _cagr([f.net_income for f in fins])
    out.historical_growth = round(hist, 3) if hist is not None else None
    base_g = _clamp(hist if hist is not None else 0.08, 0.04, 0.18)

    defs = [
        ("base", base_g, _TERMINAL, _DISCOUNT),
        ("bull", _clamp(base_g + 0.04, 0.04, 0.25), 0.05, 0.11),
        ("bear", _clamp(base_g - 0.05, 0.0, 0.18), 0.03, 0.14),
    ]
    price = out.price
    scenarios = []
    for name, g, tg, disc in defs:
        iv = _intrinsic(fcf, g, tg, disc, _YEARS, latest.shares_outstanding)
        up = ((iv - price) / price * 100) if (iv is not None and price) else None
        scenarios.append(DcfScenario(
            name=name, growth=round(g, 3), terminal_growth=tg, discount=disc, years=_YEARS,
            intrinsic_value=round(iv, 2) if iv is not None else None,
            upside_pct=round(up, 1) if up is not None else None,
        ))
    out.scenarios = scenarios
    out.note = "Equity-FCF model (OCF proxy, no capex line). A screening estimate, not a price target."
    return out
