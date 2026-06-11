"""L4b — technical indicators for the Sentiment Intelligence engine.

Pure pandas computations over a daily OHLCV frame (as returned by
`analytics.load_prices`: columns close/volume, optionally high/low).
Scoring and natural-language explanations live in the API layer
(backend.services.sentiment_service); this module only computes values.
"""

import pandas as pd

from app.analytics import metrics as M


def rsi(prices: pd.Series, window: int = 14) -> float | None:
    """Wilder's RSI of the last bar."""
    if len(prices) < window + 1:
        return None
    delta = prices.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False).mean()
    last_loss = loss.iloc[-1]
    if last_loss == 0:
        return 100.0
    rs = gain.iloc[-1] / last_loss
    return float(100 - 100 / (1 + rs))


def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict | None:
    """Returns {macd, signal, histogram, crossover} for the last bar.
    crossover: 'bullish' | 'bearish' | None (within the last 5 bars)."""
    if len(prices) < slow + signal:
        return None
    macd_line = prices.ewm(span=fast, adjust=False).mean() - prices.ewm(span=slow, adjust=False).mean()
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    crossover = None
    recent = hist.tail(5)
    if (recent > 0).iloc[-1] and (recent <= 0).any():
        crossover = "bullish"
    elif (recent < 0).iloc[-1] and (recent >= 0).any():
        crossover = "bearish"
    return {
        "macd": float(macd_line.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float(hist.iloc[-1]),
        "crossover": crossover,
    }


def bollinger(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> dict | None:
    """%B position within the bands (0 = lower band, 1 = upper band)."""
    if len(prices) < window:
        return None
    mid = prices.rolling(window).mean()
    std = prices.rolling(window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    width = upper.iloc[-1] - lower.iloc[-1]
    pct_b = (prices.iloc[-1] - lower.iloc[-1]) / width if width else 0.5
    return {
        "upper": float(upper.iloc[-1]),
        "middle": float(mid.iloc[-1]),
        "lower": float(lower.iloc[-1]),
        "pct_b": float(pct_b),
    }


def moving_average_levels(prices: pd.Series, windows=(20, 50, 100, 200)) -> dict:
    """{sma20: x, ema20: y, ...} — None where history is too short."""
    out = {}
    for w in windows:
        out[f"sma{w}"] = float(M.moving_average(prices, w, "sma").iloc[-1]) if len(prices) >= w else None
        out[f"ema{w}"] = float(M.moving_average(prices, w, "ema").iloc[-1]) if len(prices) >= w else None
    return out


def golden_cross(prices: pd.Series, short: int = 50, long: int = 200, lookback: int = 30) -> str | None:
    """'golden' / 'death' if the short SMA crossed the long SMA recently."""
    if len(prices) < long + lookback:
        return None
    s = M.moving_average(prices, short, "sma")
    l = M.moving_average(prices, long, "sma")  # noqa: E741
    diff = (s - l).tail(lookback)
    if diff.iloc[-1] > 0 and (diff <= 0).any():
        return "golden"
    if diff.iloc[-1] < 0 and (diff >= 0).any():
        return "death"
    return None


def pivot_points(df: pd.DataFrame) -> dict | None:
    """Classic floor-trader pivots from the last bar's high/low/close.
    Falls back to close-derived levels when high/low are missing."""
    last = df.iloc[-1]
    close = last.get("close")
    if close is None or close != close:
        return None
    high = last.get("high") if "high" in df.columns and last.get("high") == last.get("high") else close
    low = last.get("low") if "low" in df.columns and last.get("low") == last.get("low") else close
    p = (high + low + close) / 3
    return {
        "pivot": float(p),
        "r1": float(2 * p - low), "r2": float(p + (high - low)), "r3": float(high + 2 * (p - low)),
        "s1": float(2 * p - high), "s2": float(p - (high - low)), "s3": float(low - 2 * (high - p)),
    }


MOMENTUM_WINDOWS = {"1W": 5, "2W": 10, "1M": 22, "3M": 66, "6M": 126, "1Y": 252}


def momentum_ranges(df: pd.DataFrame) -> list[dict]:
    """Shoonya-style range sliders: low / high / current per window,
    plus the simple return over the window."""
    closes = df["close"].dropna()
    if closes.empty:
        return []
    current = float(closes.iloc[-1])
    out = []
    for label, days in MOMENTUM_WINDOWS.items():
        window = closes.tail(days)
        if len(window) < 2:
            continue
        out.append({
            "period": label,
            "low": float(window.min()),
            "high": float(window.max()),
            "current": current,
            "change": float(current / window.iloc[0] - 1),
        })
    return out


def volume_trend(df: pd.DataFrame, short: int = 10, long: int = 50) -> dict | None:
    """Ratio of recent average volume to the longer baseline."""
    if "volume" not in df.columns:
        return None
    vol = df["volume"].dropna()
    if len(vol) < long:
        return None
    recent, base = float(vol.tail(short).mean()), float(vol.tail(long).mean())
    return {"recent_avg": recent, "baseline_avg": base,
            "ratio": recent / base if base else None}
