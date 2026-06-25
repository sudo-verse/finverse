"""Earnings-growth / momentum tracker.

We only hold annual (FY) statements, so this is a year-over-year view rather
than QoQ. With no analyst estimates available, "surprise" is expressed as
*momentum*: whether the latest year's PAT growth is accelerating or
decelerating versus the prior year's. Pure compute over the financials already
in the DB; cached 10 min like the screener/radar.
"""

import time

from sqlalchemy.orm import Session

from app.db.models import Company, FinancialStatement
from backend.schemas.earnings import EarningsRow, EarningsYear, StockEarnings
from backend.services import universe_service

_CACHE_TTL = 600
_cache: tuple[float, list[EarningsRow]] | None = None
_TREND_YEARS = 6


def _growth(curr, prev):
    """YoY change as a fraction; None when prior is non-positive (turnarounds
    from a loss have no meaningful percentage)."""
    if curr is None or prev is None or prev <= 0:
        return None
    return (curr - prev) / prev


def _margin(net_income, revenue):
    if net_income is None or not revenue:
        return None
    return net_income / revenue


def _momentum(pat_yoy, prior_pat_yoy):
    """Accelerating/decelerating/steady from PAT growth vs the year before."""
    if pat_yoy is None:
        return None
    if prior_pat_yoy is None:
        return "accelerating" if pat_yoy > 0 else "decelerating"
    delta = pat_yoy - prior_pat_yoy
    if delta > 0.02:
        return "accelerating"
    if delta < -0.02:
        return "decelerating"
    return "steady"


def _annual_by_company(session: Session) -> dict[int, list[FinancialStatement]]:
    out: dict[int, list[FinancialStatement]] = {}
    for f in (
        session.query(FinancialStatement)
        .filter_by(period_type="annual")
        .order_by(FinancialStatement.company_id, FinancialStatement.period)
        .all()
    ):
        out.setdefault(f.company_id, []).append(f)
    return out


def _eps(f: FinancialStatement):
    if f is None:
        return None
    if f.eps:
        return f.eps
    if f.net_income is not None and f.shares_outstanding:
        return f.net_income / f.shares_outstanding
    return None


def _build(session: Session) -> list[EarningsRow]:
    fins = _annual_by_company(session)
    out: list[EarningsRow] = []
    for c in session.query(Company).order_by(Company.symbol).all():
        rows = fins.get(c.id, [])
        if len(rows) < 2:
            continue
        latest, prev = rows[-1], rows[-2]
        prev2 = rows[-3] if len(rows) >= 3 else None

        pat_yoy = _growth(latest.net_income, prev.net_income)
        prior_pat_yoy = _growth(prev.net_income, prev2.net_income) if prev2 else None
        m_latest = _margin(latest.net_income, latest.revenue)
        m_prev = _margin(prev.net_income, prev.revenue)
        margin_delta = (m_latest - m_prev) * 100 if (m_latest is not None and m_prev is not None) else None

        out.append(EarningsRow(
            symbol=c.symbol,
            name=c.name,
            fy=latest.period,
            revenue=latest.revenue,
            net_income=latest.net_income,
            eps=_eps(latest),
            revenue_yoy=_growth(latest.revenue, prev.revenue),
            pat_yoy=pat_yoy,
            eps_yoy=_growth(_eps(latest), _eps(prev)),
            net_margin=m_latest,
            margin_delta=round(margin_delta, 2) if margin_delta is not None else None,
            momentum=_momentum(pat_yoy, prior_pat_yoy),
            trend=[r.net_income for r in rows[-_TREND_YEARS:] if r.net_income is not None],
        ))
    return out


def _all(session: Session) -> list[EarningsRow]:
    global _cache
    now = time.time()
    if _cache and now - _cache[0] < _CACHE_TTL:
        return _cache[1]
    rows = _build(session)
    _cache = (now, rows)
    return rows


# Sanity bounds so the leaderboard surfaces real momentum rather than artifacts.
# A net margin outside ±100% means PAT exceeds revenue — almost always a
# scale-mismatched or other-income-distorted filing. Growth beyond a few
# hundred percent is a near-zero-base turnaround, not sustainable momentum; we
# cap it out of the ranking (the per-stock view keeps the full, honest history).
_MAX_GROWTH = 3.0       # +300%
_MIN_GROWTH = -0.95     # -95%
_MAX_MARGIN_DELTA = 60  # percentage points

_SORTS = {
    "pat": ("pat_yoy", lambda r: r.pat_yoy),
    "revenue": ("revenue_yoy", lambda r: r.revenue_yoy),
    "margin": ("margin_delta", lambda r: r.margin_delta),
}


def _plausible(r: EarningsRow) -> bool:
    """Drop filings whose internal scale is inconsistent (PAT > revenue)."""
    return r.net_margin is not None and abs(r.net_margin) <= 1.0


def _in_bounds(metric: str, value) -> bool:
    if value is None:
        return False
    if metric == "margin_delta":
        return abs(value) <= _MAX_MARGIN_DELTA
    return _MIN_GROWTH <= value <= _MAX_GROWTH


def tracker(session: Session, sort: str = "pat", limit: int = 50,
            universe: str | None = None) -> list[EarningsRow]:
    metric, key = _SORTS.get(sort, _SORTS["pat"])
    rows = [
        r for r in universe_service.filter_rows(_all(session), universe)
        if _plausible(r) and _in_bounds(metric, getattr(r, metric))
    ]
    rows.sort(key=lambda r: key(r) or 0, reverse=True)
    return rows[:limit]


def stock_earnings(session: Session, symbol: str) -> StockEarnings | None:
    company = session.query(Company).filter(Company.symbol == symbol.upper()).first()
    if company is None:
        return None
    rows = (
        session.query(FinancialStatement)
        .filter_by(company_id=company.id, period_type="annual")
        .order_by(FinancialStatement.period)
        .all()
    )
    years: list[EarningsYear] = []
    for i, f in enumerate(rows):
        prev = rows[i - 1] if i > 0 else None
        years.append(EarningsYear(
            fy=f.period,
            revenue=f.revenue,
            net_income=f.net_income,
            eps=_eps(f),
            revenue_yoy=_growth(f.revenue, prev.revenue) if prev else None,
            pat_yoy=_growth(f.net_income, prev.net_income) if prev else None,
            net_margin=_margin(f.net_income, f.revenue),
        ))

    latest = years[-1] if years else None
    momentum = None
    if len(years) >= 2:
        momentum = _momentum(years[-1].pat_yoy, years[-2].pat_yoy)
    return StockEarnings(
        symbol=company.symbol,
        name=company.name,
        fy=latest.fy if latest else None,
        revenue_yoy=latest.revenue_yoy if latest else None,
        pat_yoy=latest.pat_yoy if latest else None,
        momentum=momentum,
        years=years,
    )
