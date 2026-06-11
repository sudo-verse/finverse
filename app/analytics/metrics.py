"""Pure quantitative metrics computed on a price series (pandas).

All functions take a pandas Series of closing prices indexed by date and are
independent of the data source, so they're easy to test and reuse.
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252
DEFAULT_RISK_FREE = 0.06  # ~6% annual (India 10Y proxy)


def daily_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()


def cumulative_return(prices: pd.Series):
    """Total return over the whole window, e.g. 0.12 == +12%."""
    prices = prices.dropna()
    if len(prices) < 2 or prices.iloc[0] == 0:
        return None
    return float(prices.iloc[-1] / prices.iloc[0] - 1)


def annualized_return(prices: pd.Series):
    rets = daily_returns(prices)
    if rets.empty:
        return None
    return float(rets.mean() * TRADING_DAYS)


def annualized_volatility(prices: pd.Series):
    rets = daily_returns(prices)
    if len(rets) < 2:
        return None
    return float(rets.std(ddof=1) * np.sqrt(TRADING_DAYS))


def sharpe_ratio(prices: pd.Series, risk_free=DEFAULT_RISK_FREE):
    ann_ret = annualized_return(prices)
    ann_vol = annualized_volatility(prices)
    if ann_ret is None or not ann_vol:
        return None
    return float((ann_ret - risk_free) / ann_vol)


def max_drawdown(prices: pd.Series):
    """Largest peak-to-trough decline (negative number, e.g. -0.23)."""
    prices = prices.dropna()
    if len(prices) < 2:
        return None
    running_max = prices.cummax()
    drawdown = prices / running_max - 1
    return float(drawdown.min())


def moving_average(prices: pd.Series, window: int, kind="sma") -> pd.Series:
    if kind == "ema":
        return prices.ewm(span=window, adjust=False).mean()
    return prices.rolling(window=window).mean()


def latest_moving_averages(prices: pd.Series, windows=(20, 50, 200)):
    out = {}
    for w in windows:
        if len(prices.dropna()) >= w:
            out[f"sma_{w}"] = float(moving_average(prices, w, "sma").iloc[-1])
        else:
            out[f"sma_{w}"] = None
    return out


def detect_trend(prices: pd.Series, short=20, long=50):
    """Classify trend from SMA positioning + recent slope."""
    prices = prices.dropna()
    if len(prices) < long:
        return "insufficient_data"

    sma_short = moving_average(prices, short, "sma").iloc[-1]
    sma_long = moving_average(prices, long, "sma").iloc[-1]

    if sma_short > sma_long * 1.01:
        return "uptrend"
    if sma_short < sma_long * 0.99:
        return "downtrend"
    return "sideways"


def compute_all(prices: pd.Series, risk_free=DEFAULT_RISK_FREE) -> dict:
    """Bundle every metric for a price series into one dict."""
    prices = prices.dropna()
    metrics = {
        "data_points": int(len(prices)),
        "latest_price": float(prices.iloc[-1]) if len(prices) else None,
        "cumulative_return": cumulative_return(prices),
        "annualized_return": annualized_return(prices),
        "annualized_volatility": annualized_volatility(prices),
        "sharpe_ratio": sharpe_ratio(prices, risk_free),
        "max_drawdown": max_drawdown(prices),
        "trend": detect_trend(prices),
    }
    metrics.update(latest_moving_averages(prices))
    return metrics
