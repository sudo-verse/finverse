"""Relative fair-value model.

For each stock we estimate fair value from sector-relative multiples, tilted
by quality:

  • P/E leg — fair P/E = sector-median P/E × growth tilt (a faster-growing
    company than its sector earns a premium), applied to the company's earnings.
  • P/B leg — fair P/B = sector-median P/B × ROE tilt (P/B is justified by ROE).

The two legs are blended; eps and book-value-per-share are backed out of the
screener's already-guarded P/E and P/B (so the same scale guards apply). This
is a screening signal, not a price target — confidence (sector depth + how many
legs are available) is reported, and outliers are dropped from the leaderboard.

Everything is derived from `screener_service.screen()` output; cached 10 min.
"""

import statistics
import time
from collections import defaultdict

from sqlalchemy.orm import Session

from backend.schemas.valuation import ValuationOut, ValuationRow
from backend.services import screener_service, universe_service

_CACHE_TTL = 600
_cache: tuple[float, dict[str, ValuationOut]] | None = None

_PE_W = 0.6           # P/E leg weight when both legs available
_PB_W = 0.4
_TILT_LO, _TILT_HI = 0.7, 1.4     # bound the quality adjustment
_RATIO_LO, _RATIO_HI = 0.33, 3.0  # bound each leg's fair/price ratio (kills scale-artifact blowups)
_UNDERVALUED = 15.0   # % upside thresholds for the verdict
_MIN_SECTOR_N = 8     # sector multiple samples for "high" confidence


def _median(vals: list[float]) -> float | None:
    return statistics.median(vals) if vals else None


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _verdict(upside: float) -> str:
    if upside >= _UNDERVALUED:
        return "undervalued"
    if upside <= -_UNDERVALUED:
        return "overvalued"
    return "fairly valued"


def _value_one(r, smed: dict, scount: dict, mmed: dict) -> ValuationOut | None:
    price = r.price
    if not price or price <= 0:
        return None

    sector_pe = smed.get("pe") or mmed.get("pe")
    sector_pb = smed.get("pb") or mmed.get("pb")
    sector_roe = smed.get("roe") or mmed.get("roe")
    sector_g = smed.get("g")
    if sector_g is None:
        sector_g = mmed.get("g") or 0.0

    legs: list[tuple[float, float]] = []   # (fair_value, weight)
    fair_pe = pe_fair_value = None
    fair_pb = pb_fair_value = None

    # P/E leg — tilt the sector multiple by relative profit growth.
    if r.pe and r.pe > 0 and sector_pe:
        g = r.profit_growth if r.profit_growth is not None else sector_g
        tilt = _clamp((1 + max(g, -0.5)) / (1 + (sector_g or 0.0)), _TILT_LO, _TILT_HI)
        fair_pe = sector_pe * tilt
        # clamp the fair/current ratio so a scale-artifact tiny multiple can't
        # produce an absurd fair value.
        ratio = _clamp(fair_pe / r.pe, _RATIO_LO, _RATIO_HI)
        pe_fair_value = price * ratio
        legs.append((pe_fair_value, _PE_W))

    # P/B leg — tilt the sector multiple by relative ROE (P/B justified by ROE).
    if r.pb and r.pb > 0 and sector_pb:
        if r.roe is not None and sector_roe and sector_roe > 0:
            tilt = _clamp(r.roe / sector_roe, _TILT_LO, _TILT_HI)
        else:
            tilt = 1.0
        fair_pb = sector_pb * tilt
        ratio = _clamp(fair_pb / r.pb, _RATIO_LO, _RATIO_HI)
        pb_fair_value = price * ratio
        legs.append((pb_fair_value, _PB_W))

    if not legs:
        return None

    wsum = sum(w for _, w in legs)
    fair_value = sum(v * w for v, w in legs) / wsum
    if fair_value <= 0:
        return None

    upside = (fair_value - price) / price * 100
    n = scount.get("pe", 0)
    if len(legs) == 2 and n >= _MIN_SECTOR_N:
        confidence = "high"
    elif n >= 4:
        confidence = "medium"
    else:
        confidence = "low"

    return ValuationOut(
        symbol=r.symbol, name=r.name, sector=r.sector, price=round(price, 2),
        fair_value=round(fair_value, 2),
        upside_pct=round(upside, 1),
        margin_of_safety=round(max(0.0, (fair_value - price) / fair_value * 100), 1),
        verdict=_verdict(upside),
        confidence=confidence,
        pe=r.pe, sector_pe=round(sector_pe, 1) if sector_pe else None,
        fair_pe=round(fair_pe, 1) if fair_pe else None,
        pe_fair_value=round(pe_fair_value, 2) if pe_fair_value else None,
        pb=r.pb, sector_pb=round(sector_pb, 2) if sector_pb else None,
        fair_pb=round(fair_pb, 2) if fair_pb else None,
        pb_fair_value=round(pb_fair_value, 2) if pb_fair_value else None,
        method="Sector-relative multiples (P/E×growth + P/B×ROE)",
        note="Relative screening estimate, not a price target.",
    )


def _build(session: Session) -> dict[str, ValuationOut]:
    rows = screener_service.screen(session)

    sect: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"pe": [], "pb": [], "roe": [], "g": []})
    allv: dict[str, list[float]] = {"pe": [], "pb": [], "roe": [], "g": []}
    for r in rows:
        s = r.sector or "—"
        if r.pe and r.pe > 0:
            sect[s]["pe"].append(r.pe); allv["pe"].append(r.pe)
        if r.pb and r.pb > 0:
            sect[s]["pb"].append(r.pb); allv["pb"].append(r.pb)
        if r.roe and r.roe > 0:
            sect[s]["roe"].append(r.roe); allv["roe"].append(r.roe)
        if r.profit_growth is not None:
            sect[s]["g"].append(r.profit_growth); allv["g"].append(r.profit_growth)

    smed = {s: {k: _median(v) for k, v in d.items()} for s, d in sect.items()}
    scount = {s: {k: len(v) for k, v in d.items()} for s, d in sect.items()}
    mmed = {k: _median(v) for k, v in allv.items()}

    out: dict[str, ValuationOut] = {}
    for r in rows:
        s = r.sector or "—"
        v = _value_one(r, smed.get(s, {}), scount.get(s, {}), mmed)
        if v:
            out[r.symbol] = v
    return out


def _all(session: Session) -> dict[str, ValuationOut]:
    global _cache
    now = time.time()
    if _cache and now - _cache[0] < _CACHE_TTL:
        return _cache[1]
    data = _build(session)
    _cache = (now, data)
    return data


def stock(session: Session, symbol: str) -> ValuationOut | None:
    return _all(session).get(symbol.upper())


def tracker(session: Session, verdict: str | None = None, limit: int = 50,
            universe: str | None = None) -> list[ValuationRow]:
    # Medians are computed on the full universe (in _all); only the leaderboard
    # rows are narrowed to the chosen index here.
    candidates = universe_service.filter_rows(list(_all(session).values()), universe)
    rows = [
        v for v in candidates
        if v.confidence != "low" and v.upside_pct is not None and -90 <= v.upside_pct <= 200
    ]
    if verdict:
        rows = [v for v in rows if v.verdict == verdict]
    rows.sort(key=lambda v: v.upside_pct or 0, reverse=True)
    return [
        ValuationRow(
            symbol=v.symbol, name=v.name, sector=v.sector, price=v.price,
            fair_value=v.fair_value, upside_pct=v.upside_pct,
            verdict=v.verdict, confidence=v.confidence,
        )
        for v in rows[:limit]
    ]
