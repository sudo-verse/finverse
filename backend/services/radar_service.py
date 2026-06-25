"""52-week high/low radar — stocks at or near their yearly extremes.

Computed from our own price history (max high / min low over the trailing
~52 weeks) versus the latest close. Set-based SQL + one Python pass, cached
10 min like the screener. Accuracy scales with price-history depth.
"""

import math
import time
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Company, PriceHistory
from backend.schemas.radar import RadarRow, StockRange
from backend.services.screener_service import _latest_prices

_WINDOW_DAYS = 365
_cache: tuple[float, list[RadarRow]] | None = None
_CACHE_TTL = 600


def _window_hilo(session: Session) -> dict[int, tuple[float, float]]:
    """company_id -> (52w high, 52w low) over finite bars in the window."""
    cutoff = date.today() - timedelta(days=_WINDOW_DAYS)
    rows = (
        session.query(
            PriceHistory.company_id,
            func.max(PriceHistory.high).label("hi"),
            func.min(PriceHistory.low).label("lo"),
        )
        .filter(
            PriceHistory.date >= cutoff,
            PriceHistory.high.isnot(None), PriceHistory.high != float("nan"),
            PriceHistory.low.isnot(None), PriceHistory.low != float("nan"),
        )
        .group_by(PriceHistory.company_id)
        .all()
    )
    out = {}
    for cid, hi, lo in rows:
        if hi is not None and lo is not None and not math.isnan(hi) and not math.isnan(lo) and hi > lo > 0:
            out[cid] = (hi, lo)
    return out


def _metrics(price: float, hi: float, lo: float) -> dict:
    return {
        "pct_from_high": round((price - hi) / hi * 100, 2),
        "pct_from_low": round((price - lo) / lo * 100, 2),
        "pct_in_range": round((price - lo) / (hi - lo) * 100, 2),
    }


def _build(session: Session) -> list[RadarRow]:
    hilo = _window_hilo(session)
    prices = _latest_prices(session)
    names = dict(session.query(Company.id, Company.symbol).all())
    fullname = dict(session.query(Company.id, Company.name).all())

    out: list[RadarRow] = []
    for cid, (hi, lo) in hilo.items():
        price = prices.get(cid)
        if price is None or cid not in names:
            continue
        m = _metrics(price, hi, lo)
        # clamp the in-range to [0,100] (price can poke just past the window extreme)
        in_range = min(100.0, max(0.0, m["pct_in_range"]))
        out.append(RadarRow(
            symbol=names[cid], name=fullname.get(cid, ""), band="",
            price=price, high52=round(hi, 2), low52=round(lo, 2),
            pct_from_high=m["pct_from_high"], pct_from_low=m["pct_from_low"],
            pct_in_range=in_range,
        ))
    return out


def _all(session: Session) -> list[RadarRow]:
    global _cache
    if _cache and time.time() - _cache[0] < _CACHE_TTL:
        return _cache[1]
    rows = _build(session)
    _cache = (time.time(), rows)
    return rows


class RadarService:
    def screen(self, session: Session, band: str = "high", threshold: float = 3.0,
               limit: int = 100) -> list[RadarRow]:
        """Stocks within `threshold`% of their 52-week high (band="high") or
        low (band="low"), closest to the extreme first."""
        rows = _all(session)
        if band == "low":
            near = [r for r in rows if r.pct_from_low is not None and r.pct_from_low <= threshold]
            near.sort(key=lambda r: r.pct_from_low)
        else:
            band = "high"
            near = [r for r in rows if r.pct_from_high is not None and r.pct_from_high >= -threshold]
            near.sort(key=lambda r: r.pct_from_high, reverse=True)
        return [r.model_copy(update={"band": band}) for r in near[:limit]]

    def stock_range(self, session: Session, symbol: str) -> StockRange:
        company = session.query(Company).filter(Company.symbol == symbol.upper()).first()
        if company is None:
            return StockRange(symbol=symbol.upper())
        hilo = _window_hilo(session).get(company.id)
        price = _latest_prices(session).get(company.id)
        if not hilo or price is None:
            return StockRange(symbol=company.symbol, price=price)
        hi, lo = hilo
        m = _metrics(price, hi, lo)
        return StockRange(
            symbol=company.symbol, price=price, high52=round(hi, 2), low52=round(lo, 2),
            pct_from_high=m["pct_from_high"], pct_from_low=m["pct_from_low"],
            pct_in_range=min(100.0, max(0.0, m["pct_in_range"])),
            at_high=m["pct_from_high"] >= -1.0, at_low=m["pct_from_low"] <= 1.0,
        )


radar_service = RadarService()
