"""Technical-analysis layer — indicators computed from our own daily OHLCV.

Per-stock loads one company's ~250 bars and computes the full set (SMA 20/50/200,
RSI, MACD, classic pivots, 52-week position, volume) plus a composite 0-100
technical score and human-readable signals. The market screen loads only a
~95-day window per company (enough for RSI/SMA50/MACD) and reuses the cached
52-week radar for the long-term leg, so it stays within the box's memory budget.
Pure-Python maths (no pandas) on bounded data; market screen cached ~10 min.
"""

import math
import time
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.db.models import Company, PriceHistory
from backend.schemas.technicals import TechnicalRow, TechnicalSignal, TechnicalsOut
from backend.services import radar_service, universe_service
from backend.services.radar_service import radar_service as _radar

_CACHE_TTL = 600
_screen_cache: tuple[float, list[TechnicalRow]] | None = None
_DETAIL_DAYS = 400      # ~250 trading bars — enough for SMA200
_SCREEN_DAYS = 95       # ~65 trading bars — enough for RSI/SMA50/MACD


# ------------------------------------------------------------------ indicators
def _finite(x) -> bool:
    return x is not None and not math.isnan(x)


def _sma(vals: list[float], n: int) -> float | None:
    return sum(vals[-n:]) / n if len(vals) >= n else None


def _ema_series(vals: list[float], n: int) -> list[float]:
    """EMA seeded with the SMA of the first n values; returns length len-n+1."""
    if len(vals) < n:
        return []
    k = 2 / (n + 1)
    e = sum(vals[:n]) / n
    out = [e]
    for v in vals[n:]:
        e = v * k + e * (1 - k)
        out.append(e)
    return out


def _rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_g = (avg_g * (period - 1) + gains[i]) / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
    if avg_l == 0:
        return 100.0 if avg_g > 0 else 50.0   # flat series → neutral
    rs = avg_g / avg_l
    return round(100 - 100 / (1 + rs), 1)


def _macd(closes: list[float]) -> tuple[float | None, float | None, float | None]:
    """MACD line (EMA12-EMA26), signal (EMA9 of MACD), histogram."""
    e12, e26 = _ema_series(closes, 12), _ema_series(closes, 26)
    if not e26:
        return None, None, None
    n = len(e26)
    macd_series = [a - b for a, b in zip(e12[-n:], e26)]
    sig_series = _ema_series(macd_series, 9)
    if not sig_series:
        return round(macd_series[-1], 2), None, None
    macd = macd_series[-1]
    signal = sig_series[-1]
    return round(macd, 2), round(signal, 2), round(macd - signal, 2)


def _crossed(short: list[float], long: list[float], n: int, lookback: int = 5) -> bool | None:
    """Did the short SMA cross above the long SMA within `lookback` bars?
    Returns current short>long state (golden if true)."""
    if len(short) < n or len(long) < n:
        return None
    return _sma(short, n) is not None and _sma(short, n) > _sma(long, n)  # current state


# ---------------------------------------------------------------- composite
def _score_and_signals(price, sma20, sma50, sma200, rsi, macd_hist, pct_in_range):
    """Blend the available technical cues into a 0-100 score + signal chips."""
    parts: list[tuple[float, float]] = []   # (subscore 0-100, weight)
    signals: list[TechnicalSignal] = []

    def tone(b):  # bool-ish -> tone
        return "bull" if b else "bear"

    if price and sma20:
        up = price > sma20
        parts.append((100 if up else 0, 0.15))
        signals.append(TechnicalSignal(label="vs 20-DMA", value=f"{'above' if up else 'below'}", tone=tone(up)))
    if price and sma50:
        up = price > sma50
        parts.append((100 if up else 0, 0.20))
        signals.append(TechnicalSignal(label="vs 50-DMA", value=f"{'above' if up else 'below'}", tone=tone(up)))
    if price and sma200:
        up = price > sma200
        parts.append((100 if up else 0, 0.25))
        signals.append(TechnicalSignal(label="vs 200-DMA", value=f"{'above' if up else 'below'}", tone=tone(up)))
    if sma50 and sma200:
        golden = sma50 > sma200
        signals.append(TechnicalSignal(label=golden and "Golden cross" or "Death cross",
                                        value="50 over 200" if golden else "50 under 200",
                                        tone=tone(golden)))
    if rsi is not None:
        # 50 is neutral; reward momentum but flag overbought/oversold extremes.
        sub = max(0.0, min(100.0, (rsi - 30) / 40 * 100))
        parts.append((sub, 0.20))
        if rsi >= 70:
            signals.append(TechnicalSignal(label="RSI", value=f"{rsi:.0f} · overbought", tone="bear"))
        elif rsi <= 30:
            signals.append(TechnicalSignal(label="RSI", value=f"{rsi:.0f} · oversold", tone="bull"))
        else:
            signals.append(TechnicalSignal(label="RSI", value=f"{rsi:.0f}", tone="bull" if rsi >= 50 else "bear"))
    if macd_hist is not None:
        up = macd_hist > 0
        parts.append((100 if up else 0, 0.10))
        signals.append(TechnicalSignal(label="MACD", value="bullish" if up else "bearish", tone=tone(up)))
    if pct_in_range is not None:
        parts.append((pct_in_range, 0.10))

    if not parts:
        return None, None, signals
    wsum = sum(w for _, w in parts)
    score = sum(s * w for s, w in parts) / wsum
    trend = "bullish" if score >= 60 else "bearish" if score <= 40 else "neutral"
    return round(score, 1), trend, signals


# ------------------------------------------------------------------ per-stock
def technicals(session: Session, symbol: str) -> TechnicalsOut | None:
    company = session.query(Company).filter(Company.symbol == symbol.upper()).first()
    if company is None:
        return None
    cutoff = date.today() - timedelta(days=_DETAIL_DAYS)
    bars = (
        session.query(PriceHistory.high, PriceHistory.low, PriceHistory.close, PriceHistory.volume)
        .filter(PriceHistory.company_id == company.id, PriceHistory.date >= cutoff,
                PriceHistory.close.isnot(None))
        .order_by(PriceHistory.date)
        .all()
    )
    clean = [b for b in bars if _finite(b.close)]
    closes = [b.close for b in clean]
    if len(closes) < 15:        # need at least an RSI window
        return TechnicalsOut(symbol=company.symbol, name=company.name, bars=len(closes))

    price = closes[-1]
    sma20, sma50, sma200 = _sma(closes, 20), _sma(closes, 50), _sma(closes, 200)
    rsi = _rsi(closes)
    macd, macd_sig, macd_hist = _macd(closes)

    # classic floor pivots from the most recent finite bar
    last = clean[-1]
    pivot = r1 = r2 = s1 = s2 = None
    if _finite(last.high) and _finite(last.low) and _finite(last.close):
        pivot = (last.high + last.low + last.close) / 3
        r1, s1 = 2 * pivot - last.low, 2 * pivot - last.high
        r2, s2 = pivot + (last.high - last.low), pivot - (last.high - last.low)

    rng = _radar.stock_range(session, company.symbol)
    vols = [b.volume for b in clean if b.volume]
    vol_avg20 = sum(vols[-20:]) / len(vols[-20:]) if vols else None

    score, trend, signals = _score_and_signals(
        price, sma20, sma50, sma200, rsi, macd_hist, rng.pct_in_range,
    )

    def r(x, d=2):
        return round(x, d) if x is not None else None

    return TechnicalsOut(
        symbol=company.symbol, name=company.name, price=r(price), score=score, trend=trend,
        bars=len(closes),
        sma20=r(sma20), sma50=r(sma50), sma200=r(sma200),
        golden_cross=(sma50 > sma200) if (sma50 and sma200) else None,
        rsi=rsi, macd=macd, macd_signal=macd_sig, macd_hist=macd_hist,
        pivot=r(pivot), r1=r(r1), r2=r(r2), s1=r(s1), s2=r(s2),
        high52=rng.high52, low52=rng.low52, pct_from_high=rng.pct_from_high,
        pct_in_range=rng.pct_in_range,
        vol_latest=float(last.volume) if last.volume else None, vol_avg20=r(vol_avg20, 0),
        signals=signals,
    )


# --------------------------------------------------------------- market screen
def _build_screen(session: Session) -> list[TechnicalRow]:
    cutoff = date.today() - timedelta(days=_SCREEN_DAYS)
    rows = (
        session.query(PriceHistory.company_id, PriceHistory.close)
        .filter(PriceHistory.date >= cutoff, PriceHistory.close.isnot(None))
        .order_by(PriceHistory.company_id, PriceHistory.date)
        .all()
    )
    by_co: dict[int, list[float]] = {}
    for cid, close in rows:
        if _finite(close):
            by_co.setdefault(cid, []).append(close)

    names = dict(session.query(Company.id, Company.symbol).all())
    fullname = dict(session.query(Company.id, Company.name).all())
    sectors = dict(session.query(Company.id, Company.sector).all())
    rng = {r.symbol: r for r in radar_service._all(session)}

    out: list[TechnicalRow] = []
    for cid, closes in by_co.items():
        if len(closes) < 20 or cid not in names:
            continue
        sym = names[cid]
        price = closes[-1]
        sma50 = _sma(closes, 50)
        rsi = _rsi(closes)
        _, _, macd_hist = _macd(closes)
        pir = rng[sym].pct_in_range if sym in rng else None
        score, trend, _ = _score_and_signals(price, _sma(closes, 20), sma50, None, rsi, macd_hist, pir)
        if score is None:
            continue
        out.append(TechnicalRow(
            symbol=sym, name=fullname.get(cid, ""), sector=sectors.get(cid),
            price=round(price, 2), score=score, trend=trend, rsi=rsi, macd_hist=macd_hist,
            above_sma50=(price > sma50) if sma50 else None, pct_in_range=pir,
        ))
    return out


def _screen_all(session: Session) -> list[TechnicalRow]:
    global _screen_cache
    now = time.time()
    if _screen_cache and now - _screen_cache[0] < _CACHE_TTL:
        return _screen_cache[1]
    rows = _build_screen(session)
    _screen_cache = (now, rows)
    return rows


def screen(session: Session, signal: str = "bullish", limit: int = 50,
           universe: str | None = None) -> list[TechnicalRow]:
    """Universe ranked by composite technical score. signal="bullish" → strongest
    first; "bearish" → weakest first."""
    rows = universe_service.filter_rows(_screen_all(session), universe)
    rows = sorted(rows, key=lambda r: r.score, reverse=(signal != "bearish"))
    return rows[:limit]
