"""Composite Conviction Score — the synthesis layer over the signal feeds.

For every stock we already compute, in isolation: relative valuation upside,
earnings momentum, smart-money (FII+DII) accumulation, insider/SAST direction,
technical position in the 52-week range and news sentiment. This service
normalises each into a 0-100 sub-score (higher = more bullish), blends the
available ones by weight, and reports the full breakdown so the headline number
is always explainable.

Everything is sourced from the existing cached services / persisted tables, so
the heavy work is amortised. Built once over the universe and cached ~10 min
like the screener/valuation/earnings trackers.
"""

import time
from collections import defaultdict

from sqlalchemy.orm import Session

from app.db.models import Company, SentimentScore, Shareholding
from backend.schemas.conviction import ConvictionPillar, ConvictionRow
from backend.services import (
    earnings_service,
    insider_service,
    radar_service,
    universe_service,
    valuation_service,
)

_CACHE_TTL = 600
_cache: tuple[float, dict[str, ConvictionRow]] | None = None

# Pillar weights when present; renormalised over whatever data a stock has.
_WEIGHTS = {
    "value": 0.24,
    "momentum": 0.20,
    "smart_money": 0.20,
    "insider": 0.14,
    "technical": 0.12,
    "sentiment": 0.10,
}
_LABELS = {
    "value": "Valuation",
    "momentum": "Earnings momentum",
    "smart_money": "Smart money",
    "insider": "Insider / SAST",
    "technical": "52-week trend",
    "sentiment": "News & mood",
}
_MIN_PILLARS = 3            # need at least this many to rank a stock
_UP, _DOWN = 58.0, 42.0     # sub-score thresholds for an up / down chip


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _signal(score: float | None) -> str:
    if score is None:
        return "na"
    if score >= _UP:
        return "up"
    if score <= _DOWN:
        return "down"
    return "neutral"


def _verdict(score: float) -> str:
    if score >= 68:
        return "high conviction"
    if score >= 56:
        return "constructive"
    if score >= 44:
        return "neutral"
    return "weak"


# ---------------------------------------------------------------- pillar inputs
def _smart_money(session: Session) -> dict[str, float]:
    """symbol -> QoQ change (pp) in institutional (FII+DII) holding.

    FII and DII legs are tracked independently (each needs two consecutive
    non-null snapshots) and summed, so a missing leg never fakes a jump."""
    rows = (
        session.query(
            Company.symbol,
            Shareholding.period_date,
            Shareholding.fii_pct,
            Shareholding.dii_pct,
        )
        .join(Company, Company.id == Shareholding.company_id)
        .order_by(Shareholding.company_id, Shareholding.period_date.desc())
        .all()
    )
    snaps: dict[str, list[tuple]] = defaultdict(list)
    for sym, _pd, fii, dii in rows:
        snaps[sym].append((fii, dii))

    out: dict[str, float] = {}
    for sym, s in snaps.items():
        if len(s) < 2:
            continue
        (lf, ld), (pf, pd_) = s[0], s[1]
        change = 0.0
        have = False
        if lf is not None and pf is not None:
            change += lf - pf
            have = True
        if ld is not None and pd_ is not None:
            change += ld - pd_
            have = True
        if have:
            out[sym] = change
    return out


def _insider(days: int = 30) -> dict[str, float]:
    """symbol -> directional SAST sub-score 0-100 over the window.

    Direction is scale-free: weighted acquisition vs sale filings (promoter
    filings count double — the strongest 'skin in the game' signal)."""
    bull: dict[str, float] = defaultdict(float)
    bear: dict[str, float] = defaultdict(float)
    for r in insider_service.sast_feed(days=days, limit=1000):
        if not r.symbol or not r.action:
            continue
        a = r.action.lower()
        w = 2.0 if r.is_promoter else 1.0
        if a.startswith("sale") or a.startswith("dispos"):
            bear[r.symbol] += w
        elif a.startswith("acq") or a.startswith("buy") or a.startswith("purch"):
            bull[r.symbol] += w
    out: dict[str, float] = {}
    for sym in set(bull) | set(bear):
        b, s = bull[sym], bear[sym]
        if b + s == 0:
            continue
        out[sym] = _clamp(50 + 50 * (b - s) / (b + s))
    return out


def _sentiment(session: Session) -> dict[str, float]:
    """symbol -> latest news+market 'mood' read (0-100).

    Deliberately blends only the news and market pillars of the stored sentiment
    snapshot — the fundamental/technical/ownership pillars are already covered by
    conviction's own value/technical/smart-money pillars, so using them here
    would double-count. The newest snapshot with either value wins."""
    rows = (
        session.query(SentimentScore.symbol, SentimentScore.news,
                      SentimentScore.market, SentimentScore.date)
        .order_by(SentimentScore.symbol, SentimentScore.date.desc())
        .all()
    )
    out: dict[str, float] = {}
    for sym, news, market, _d in rows:
        if sym in out:
            continue                 # already took this symbol's newest with data
        vals = [v for v in (news, market) if v is not None]
        if vals:
            out[sym] = sum(vals) / len(vals)
    return out


# ------------------------------------------------------------- pillar scorers
def _value_pillar(v) -> ConvictionPillar | None:
    if v is None or v.upside_pct is None:
        return None
    up = v.upside_pct
    score = _clamp(50 + up * 1.25)            # +40% upside -> 100, -40% -> 0
    return ConvictionPillar(
        key="value", label=_LABELS["value"], score=round(score, 1),
        weight=_WEIGHTS["value"], signal=_signal(score),
        detail=f"{'+' if up >= 0 else ''}{up:.0f}% to fair value",
    )


def _momentum_pillar(e) -> ConvictionPillar | None:
    if e is None or e.pat_yoy is None:
        return None
    g = max(-0.5, min(1.0, e.pat_yoy))
    score = (g + 0.5) / 1.5 * 100             # -50% -> 0, +100% -> 100
    tag = e.momentum
    if tag == "accelerating":
        score += 8
    elif tag == "decelerating":
        score -= 8
    score = _clamp(score)
    detail = f"PAT {'+' if e.pat_yoy >= 0 else ''}{e.pat_yoy * 100:.0f}% YoY"
    if tag:
        detail += f", {tag}"
    return ConvictionPillar(
        key="momentum", label=_LABELS["momentum"], score=round(score, 1),
        weight=_WEIGHTS["momentum"], signal=_signal(score), detail=detail,
    )


def _smart_pillar(change: float | None) -> ConvictionPillar | None:
    if change is None:
        return None
    score = _clamp(50 + change * 25)          # +2pp -> 100, -2pp -> 0
    return ConvictionPillar(
        key="smart_money", label=_LABELS["smart_money"], score=round(score, 1),
        weight=_WEIGHTS["smart_money"], signal=_signal(score),
        detail=f"FII+DII {'+' if change >= 0 else ''}{change:.2f}pp QoQ",
    )


def _insider_pillar(score: float | None) -> ConvictionPillar | None:
    if score is None:
        return None
    if score >= _UP:
        d = "net insider buying"
    elif score <= _DOWN:
        d = "net insider selling"
    else:
        d = "mixed insider activity"
    return ConvictionPillar(
        key="insider", label=_LABELS["insider"], score=round(score, 1),
        weight=_WEIGHTS["insider"], signal=_signal(score), detail=d,
    )


def _technical_pillar(r) -> ConvictionPillar | None:
    if r is None or r.pct_in_range is None:
        return None
    score = _clamp(r.pct_in_range)
    return ConvictionPillar(
        key="technical", label=_LABELS["technical"], score=round(score, 1),
        weight=_WEIGHTS["technical"], signal=_signal(score),
        detail=f"{score:.0f}% up its 52-week range",
    )


def _sentiment_pillar(score: float | None) -> ConvictionPillar | None:
    if score is None:
        return None
    s = _clamp(score)
    return ConvictionPillar(
        key="sentiment", label=_LABELS["sentiment"], score=round(s, 1),
        weight=_WEIGHTS["sentiment"], signal=_signal(s),
        detail=f"news & mood {s:.0f}/100",
    )


def _build(session: Session) -> dict[str, ConvictionRow]:
    vals = valuation_service._all(session)                       # symbol -> ValuationOut
    earn = {e.symbol: e for e in earnings_service._all(session)}
    radar = {r.symbol: r for r in radar_service._all(session)}
    smart = _smart_money(session)
    insider = _insider()
    senti = _sentiment(session)

    names = dict(session.query(Company.symbol, Company.name).all())
    sectors = dict(session.query(Company.symbol, Company.sector).all())

    symbols = set(vals) | set(earn) | set(radar) | set(smart) | set(insider) | set(senti)
    out: dict[str, ConvictionRow] = {}

    for sym in symbols:
        v = vals.get(sym)
        pillars = [
            _value_pillar(v),
            _momentum_pillar(earn.get(sym)),
            _smart_pillar(smart.get(sym)),
            _insider_pillar(insider.get(sym)),
            _technical_pillar(radar.get(sym)),
            _sentiment_pillar(senti.get(sym)),
        ]
        present = [p for p in pillars if p is not None]
        if len(present) < _MIN_PILLARS:
            continue

        wsum = sum(p.weight for p in present)
        score = sum((p.score or 0) * p.weight for p in present) / wsum

        sector = (v.sector if v else None) or sectors.get(sym)
        name = (v.name if v else None) or names.get(sym, sym)
        out[sym] = ConvictionRow(
            symbol=sym, name=name, sector=sector,
            score=round(score, 1), verdict=_verdict(score),
            coverage=len(present),
            # strongest deviations from neutral first, so the "why" leads.
            pillars=sorted(present, key=lambda p: abs((p.score or 50) - 50), reverse=True),
        )
    return out


def _all(session: Session) -> dict[str, ConvictionRow]:
    global _cache
    now = time.time()
    if _cache and now - _cache[0] < _CACHE_TTL:
        return _cache[1]
    data = _build(session)
    _cache = (now, data)
    return data


def leaderboard(session: Session, order: str = "top", limit: int = 50,
                min_coverage: int = 3, universe: str | None = None) -> list[ConvictionRow]:
    """Stocks ranked by composite conviction. order="top" → highest first,
    "bottom" → lowest first (avoid / short candidates)."""
    rows = [
        r for r in universe_service.filter_rows(list(_all(session).values()), universe)
        if r.coverage >= min_coverage
    ]
    rows.sort(key=lambda r: r.score, reverse=(order != "bottom"))
    return rows[:limit]


def stock(session: Session, symbol: str) -> ConvictionRow | None:
    return _all(session).get(symbol.upper())
