"""Per-stock red flags — surveillance (ASM/GSM), promoter pledge and a
leverage-based financial-stress read.

Surveillance comes from `surveillance_service`; pledge from NSE's per-symbol
`corporate-pledgedata` (best-effort, cached); stress is computed from the latest
annual statement (we lack current-assets/retained-earnings for a full Altman Z,
so this is an honest leverage/solvency proxy, not a bankruptcy score).
"""

import time

from sqlalchemy.orm import Session

from app.db.models import Company, FinancialStatement
from backend.schemas.red_flags import RedFlag, RedFlagsOut, SurveillanceRow
from backend.services import surveillance_service

_PLEDGE_URL = "https://www.nseindia.com/api/corporate-pledgedata"
_PLEDGE_TTL = 3600
_pledge_cache: dict[str, tuple[float, tuple]] = {}


def _num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _pledge(symbol: str) -> tuple[float | None, float | None]:
    """(pledged % of promoter shares, promoter holding %). Best-effort."""
    sym = symbol.upper()
    hit = _pledge_cache.get(sym)
    now = time.time()
    if hit and now - hit[0] < _PLEDGE_TTL:
        return hit[1]
    result: tuple[float | None, float | None] = (None, None)
    try:
        from app.market import nse_shp

        d = nse_shp._sess().get(_PLEDGE_URL, params={"symbol": sym}, timeout=20).json()
        data = d.get("data") or []
        if data:
            latest = data[0]
            result = (_num(latest.get("percSharesPledged")), _num(latest.get("percPromoterShares")))
    except Exception:
        pass
    _pledge_cache[sym] = (now, result)
    return result


# Leverage ratios are meaningless for lenders/insurers (deposits & float are
# "liabilities" but not distress), so the stress read is skipped for them.
_FINANCIAL_HINTS = ("bank", "financ", "nbfc", "insur", "capital market", "broker", "amc", "asset management")


def _is_financial(company: Company | None) -> bool:
    if company is None:
        return False
    blob = f"{company.industry or ''} {company.sector or ''}".lower()
    return any(h in blob for h in _FINANCIAL_HINTS)


def _latest_annual(session: Session, company_id: int) -> FinancialStatement | None:
    return (
        session.query(FinancialStatement)
        .filter_by(company_id=company_id, period_type="annual")
        .order_by(FinancialStatement.period.desc())
        .first()
    )


def stock_red_flags(session: Session, symbol: str) -> RedFlagsOut:
    sym = symbol.upper()
    company = session.query(Company).filter(Company.symbol == sym).first()
    out = RedFlagsOut(symbol=sym)
    flags: list[RedFlag] = []

    # --- surveillance (ASM/GSM) ---
    surv = surveillance_service.flags(sym)
    if surv:
        out.asm = surv.get("asm")
        out.gsm = surv.get("gsm")
        out.surveillance_desc = surv.get("desc")
        if out.gsm:
            flags.append(RedFlag(label="GSM surveillance", detail=out.gsm, severity="high"))
        if out.asm:
            flags.append(RedFlag(label="ASM surveillance", detail=out.asm, severity="medium"))

    # --- promoter pledge ---
    pledged, promo = _pledge(sym)
    out.pledged_pct, out.promoter_holding_pct = pledged, promo
    if pledged is not None and pledged > 0:
        sev = "high" if pledged >= 50 else "medium" if pledged >= 15 else "low"
        flags.append(RedFlag(label="Promoter pledging", detail=f"{pledged:.1f}% of promoter shares pledged", severity=sev))

    # --- leverage / financial stress (skipped for lenders/insurers) ---
    f = _latest_annual(session, company.id) if company else None
    is_fin = _is_financial(company)
    if f and f.total_assets:
        ta = f.total_assets
        lev = (f.total_liabilities / ta) if f.total_liabilities is not None else None
        eq = (f.total_equity / ta) if f.total_equity is not None else None
        out.leverage, out.equity_ratio = (round(lev, 3) if lev is not None else None,
                                          round(eq, 3) if eq is not None else None)
        neg_ocf = f.operating_cash_flow is not None and f.operating_cash_flow < 0
        neg_ebit = f.ebit is not None and f.ebit < 0
        # Leverage/cash-flow distress signals don't apply to lenders/insurers.
        if not is_fin:
            if (lev is not None and lev > 0.8) or (eq is not None and eq < 0.1) or (neg_ocf and neg_ebit):
                out.stress = "high"
            elif (lev is not None and lev > 0.6) or (eq is not None and eq < 0.25) or neg_ocf:
                out.stress = "elevated"
            else:
                out.stress = "low"
            if out.stress == "high":
                flags.append(RedFlag(label="High financial stress",
                                     detail=f"leverage {lev:.0%}" if lev is not None else "weak balance sheet",
                                     severity="high"))
            elif out.stress == "elevated":
                flags.append(RedFlag(label="Elevated leverage",
                                     detail=f"liabilities {lev:.0%} of assets" if lev is not None else None,
                                     severity="medium"))
            if neg_ocf:
                flags.append(RedFlag(label="Negative operating cash flow", detail="latest FY", severity="medium"))

    if not flags:
        flags.append(RedFlag(label="No major red flags", detail="not under NSE surveillance; leverage normal", severity="info"))
    out.flags = flags
    return out


def surveillance_feed() -> list[SurveillanceRow]:
    return [SurveillanceRow(**r) for r in surveillance_service.feed()]
