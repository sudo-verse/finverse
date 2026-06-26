"""Curated thematic baskets (smallcase-style).

Hand-picked themes whose equal-weighted return is computed from our own price
history — no new data, and it ties the rest of the app together (each basket
links to its constituents' full analysis). Cached ~10 min.
"""

import math
import time
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.db.models import Company, PriceHistory
from backend.schemas.basket import BasketConstituent, BasketDetail, BasketRow

# key -> (name, thesis, [symbols])
_BASKETS: dict[str, tuple[str, str, list[str]]] = {
    "heavyweights": ("Index Heavyweights", "The largest, most liquid names that drive the Nifty.",
                     ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "LT", "SBIN", "BHARTIARTL", "AXISBANK"]),
    "private_banks": ("Private Banks", "Leading private-sector lenders.",
                      ["HDFCBANK", "ICICIBANK", "AXISBANK", "KOTAKBANK", "INDUSINDBK", "IDFCFIRSTB", "FEDERALBNK", "BANDHANBNK"]),
    "it_majors": ("IT Majors", "Large-cap Indian IT services exporters.",
                  ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "PERSISTENT", "COFORGE", "MPHASIS"]),
    "auto": ("Auto & Ancillaries", "Vehicle makers and key component suppliers.",
             ["MARUTI", "M&M", "TATAMOTORS", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO", "TVSMOTOR", "BOSCHLTD", "MOTHERSON"]),
    "pharma": ("Pharma & Healthcare", "Drug makers and hospital chains.",
               ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP", "LUPIN", "AUROPHARMA", "TORNTPHARM", "ALKEM"]),
    "fmcg": ("FMCG / Defensives", "Steady consumer staples — lower beta.",
             ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR", "MARICO", "GODREJCP", "COLPAL", "TATACONSUM"]),
    "psu": ("PSU Pack", "State-owned banks, energy and defence.",
            ["SBIN", "NTPC", "POWERGRID", "ONGC", "COALINDIA", "BEL", "HAL", "IOC", "BPCL", "PFC"]),
    "capex": ("Capex & Infra", "Capital-goods, construction and power beneficiaries of the capex cycle.",
              ["LT", "SIEMENS", "ABB", "BEL", "CUMMINSIND", "BHEL", "THERMAX", "POWERGRID", "NTPC"]),
}

_CACHE_TTL = 600
_cache: tuple[float, dict] | None = None


def _finite(x):
    return x is not None and not math.isnan(x)


def _ret(closes: list[tuple], bars: int) -> float | None:
    """Return over the last `bars` rows of (date, close), as a fraction."""
    if len(closes) <= bars:
        return None
    last = closes[-1][1]
    prev = closes[-1 - bars][1]
    if not _finite(last) or not _finite(prev) or prev <= 0:
        return None
    return (last - prev) / prev


def _build(session: Session) -> dict:
    symbols = sorted({s for _, _, syms in _BASKETS.values() for s in syms})
    cutoff = date.today() - timedelta(days=400)
    rows = (
        session.query(Company.symbol, PriceHistory.date, PriceHistory.close)
        .join(PriceHistory, PriceHistory.company_id == Company.id)
        .filter(Company.symbol.in_(symbols), PriceHistory.date >= cutoff,
                PriceHistory.close.isnot(None))
        .order_by(Company.symbol, PriceHistory.date)
        .all()
    )
    series: dict[str, list[tuple]] = {}
    for sym, d, c in rows:
        if _finite(c):
            series.setdefault(sym, []).append((d, c))
    names = dict(session.query(Company.symbol, Company.name).filter(Company.symbol.in_(symbols)).all())

    def avg(vals):
        vals = [v for v in vals if v is not None]
        return round(sum(vals) / len(vals) * 100, 1) if vals else None   # percent

    out: dict[str, BasketDetail] = {}
    for key, (name, thesis, syms) in _BASKETS.items():
        cons: list[BasketConstituent] = []
        for s in syms:
            cl = series.get(s, [])
            cons.append(BasketConstituent(
                symbol=s, name=names.get(s), price=round(cl[-1][1], 2) if cl else None,
                ret_1m=round(_ret(cl, 21) * 100, 1) if _ret(cl, 21) is not None else None,
                ret_3m=round(_ret(cl, 63) * 100, 1) if _ret(cl, 63) is not None else None,
                ret_1y=round(_ret(cl, 252) * 100, 1) if _ret(cl, 252) is not None else None,
            ))
        r1 = avg([_ret(series.get(s, []), 21) for s in syms])
        r3 = avg([_ret(series.get(s, []), 63) for s in syms])
        r12 = avg([_ret(series.get(s, []), 252) for s in syms])
        top = [c.symbol for c in sorted(cons, key=lambda c: c.ret_1m if c.ret_1m is not None else -999, reverse=True)[:3]]
        out[key] = BasketDetail(key=key, name=name, thesis=thesis, count=len(syms),
                                ret_1m=r1, ret_3m=r3, ret_1y=r12, top=top, constituents=cons)
    return out


def _all(session: Session) -> dict:
    global _cache
    now = time.time()
    if _cache and now - _cache[0] < _CACHE_TTL:
        return _cache[1]
    data = _build(session)
    _cache = (now, data)
    return data


def list_baskets(session: Session) -> list[BasketRow]:
    rows = [BasketRow(**{k: getattr(b, k) for k in BasketRow.model_fields})
            for b in _all(session).values()]
    rows.sort(key=lambda b: b.ret_3m if b.ret_3m is not None else -999, reverse=True)
    return rows


def basket(session: Session, key: str) -> BasketDetail | None:
    return _all(session).get(key)
