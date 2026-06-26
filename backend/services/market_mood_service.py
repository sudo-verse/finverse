"""Market Mood Index — a single 0-100 fear↔greed gauge for the whole market.

Derived from market breadth, not a black box: the share of stocks trading above
their 50-day average, the average position in the 52-week range, and the share
with bullish MACD momentum. All three come from the already-cached technical
screen, so this is nearly free. Computed over the Nifty 500 (liquid names with
real price history); cached ~5 min.
"""

import time

from sqlalchemy.orm import Session

from backend.schemas.market_mood import MarketMoodOut, MoodComponent
from backend.services import technical_service, universe_service

_CACHE_TTL = 300
_cache: tuple[float, MarketMoodOut] | None = None

_WEIGHTS = {"breadth": 0.4, "range": 0.3, "momentum": 0.3}


def _zone(v: float) -> str:
    if v < 25:
        return "Extreme Fear"
    if v < 45:
        return "Fear"
    if v <= 55:
        return "Neutral"
    if v <= 75:
        return "Greed"
    return "Extreme Greed"


def _mean(vals: list[float]) -> float | None:
    return sum(vals) / len(vals) if vals else None


def _build(session: Session) -> MarketMoodOut:
    # Reuse the cached technical screen over the liquid Nifty 500 universe.
    rows = universe_service.filter_rows(technical_service._screen_all(session), "nifty500")
    if not rows:
        rows = technical_service._screen_all(session)

    breadth = _mean([100.0 if r.above_sma50 else 0.0 for r in rows if r.above_sma50 is not None])
    range_pos = _mean([r.pct_in_range for r in rows if r.pct_in_range is not None])
    momentum = _mean([100.0 if (r.macd_hist or 0) > 0 else 0.0 for r in rows if r.macd_hist is not None])

    parts: list[tuple[str, float, float]] = []   # (key, value, weight)
    if breadth is not None:
        parts.append(("breadth", breadth, _WEIGHTS["breadth"]))
    if range_pos is not None:
        parts.append(("range", range_pos, _WEIGHTS["range"]))
    if momentum is not None:
        parts.append(("momentum", momentum, _WEIGHTS["momentum"]))

    if not parts:
        return MarketMoodOut(value=50.0, zone="Neutral", components=[], sample=0)

    wsum = sum(w for _, _, w in parts)
    value = sum(v * w for _, v, w in parts) / wsum

    labels = {"breadth": "Above 50-DMA", "range": "52-week position", "momentum": "Bullish MACD"}
    return MarketMoodOut(
        value=round(value, 1),
        zone=_zone(value),
        components=[MoodComponent(label=labels[k], value=round(v, 1)) for k, v, _ in parts],
        sample=len(rows),
    )


def compute(session: Session) -> MarketMoodOut:
    global _cache
    now = time.time()
    if _cache and now - _cache[0] < _CACHE_TTL:
        return _cache[1]
    out = _build(session)
    _cache = (now, out)
    return out
