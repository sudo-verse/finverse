"""Schemas for the technical-analysis layer.

Indicators (moving averages, RSI, MACD, pivots, 52-week position, volume) are
computed from our own daily OHLCV history — no new data source. Per-stock gives
the full picture; the market screen ranks a universe by a composite technical
score. A trading-signal view, not advice.
"""

from backend.schemas.common import APIModel


class TechnicalSignal(APIModel):
    label: str
    value: str | None = None
    tone: str            # bull | bear | neutral


class TechnicalsOut(APIModel):
    symbol: str
    name: str
    price: float | None = None
    score: float | None = None        # 0-100 composite, higher = more bullish
    trend: str | None = None          # bullish | neutral | bearish
    bars: int = 0                     # how many daily bars were available

    # moving averages
    sma20: float | None = None
    sma50: float | None = None
    sma200: float | None = None
    golden_cross: bool | None = None  # SMA50 above SMA200 (long-term up)

    # oscillators
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None

    # classic floor pivots (from the latest bar)
    pivot: float | None = None
    r1: float | None = None
    r2: float | None = None
    s1: float | None = None
    s2: float | None = None

    # 52-week range
    high52: float | None = None
    low52: float | None = None
    pct_from_high: float | None = None
    pct_in_range: float | None = None

    # volume
    vol_latest: float | None = None
    vol_avg20: float | None = None

    signals: list[TechnicalSignal] = []


class TechnicalRow(APIModel):
    symbol: str
    name: str
    sector: str | None = None
    price: float | None = None
    score: float                      # 0-100 composite
    trend: str                        # bullish | neutral | bearish
    rsi: float | None = None
    macd_hist: float | None = None
    above_sma50: bool | None = None
    pct_in_range: float | None = None
