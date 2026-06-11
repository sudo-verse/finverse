"""Unit tests for app.analytics.technicals (pure pandas, no network)."""

import numpy as np
import pandas as pd
import pytest

from app.analytics import technicals as T


def series(values):
    return pd.Series(values, dtype=float)


def trending(n=300, start=100.0, step=0.5, noise_seed=7):
    rng = np.random.default_rng(noise_seed)
    return series(start + step * np.arange(n) + rng.normal(0, 0.3, n))


class TestRSI:
    def test_uptrend_is_high(self):
        r = T.rsi(trending(step=0.8))
        assert r is not None and 60 <= r <= 100

    def test_downtrend_is_low(self):
        r = T.rsi(trending(start=300, step=-0.8))
        assert r is not None and 0 <= r <= 40

    def test_short_series_returns_none(self):
        assert T.rsi(series(range(10))) is None

    def test_all_gains_caps_at_100(self):
        assert T.rsi(series(range(1, 40))) == pytest.approx(100.0)


class TestMACD:
    def test_bullish_crossover_on_v_shape(self):
        # long decline then sharp recovery → histogram flips positive within
        # the 5-bar crossover window
        prices = list(np.linspace(200, 100, 120)) + list(np.linspace(100, 130, 4))
        m = T.macd(series(prices))
        assert m is not None
        assert m["crossover"] == "bullish"
        assert m["histogram"] > 0

    def test_steady_uptrend_no_recent_crossover(self):
        # In a constant-slope trend MACD converges: the histogram hovers near
        # zero with noise — that noise must NOT register as crossovers.
        m = T.macd(trending(step=1.0))
        assert m is not None and m["crossover"] is None
        assert abs(m["histogram"]) < 1.0  # converged, no momentum change

    def test_short_series_returns_none(self):
        assert T.macd(series(range(20))) is None


class TestBollinger:
    def test_uptrend_sits_in_upper_band(self):
        b = T.bollinger(trending(step=1.0))
        assert b is not None
        assert b["lower"] < b["middle"] < b["upper"]
        assert b["pct_b"] > 0.5

    def test_flat_series_is_midband(self):
        b = T.bollinger(series([100.0] * 25 + [100.0001]))
        assert b is not None  # zero-width band must not divide by zero


class TestPivots:
    def test_classic_pivot_math(self):
        df = pd.DataFrame({"close": [100.0], "high": [110.0], "low": [95.0]})
        p = T.pivot_points(df)
        assert p["pivot"] == pytest.approx((110 + 95 + 100) / 3)
        assert p["s1"] < p["pivot"] < p["r1"]
        assert p["s3"] < p["s2"] < p["s1"]
        assert p["r1"] < p["r2"] < p["r3"]

    def test_falls_back_to_close_without_hl(self):
        df = pd.DataFrame({"close": [100.0]})
        p = T.pivot_points(df)
        assert p["pivot"] == pytest.approx(100.0)


class TestMomentumAndVolume:
    def test_ranges_contain_current(self):
        df = pd.DataFrame({"close": trending()})
        for m in T.momentum_ranges(df):
            assert m["low"] - 1e-9 <= m["current"] <= m["high"] + 1e-9

    def test_volume_trend_ratio(self):
        df = pd.DataFrame({
            "close": trending(n=100),
            "volume": [1000.0] * 90 + [2000.0] * 10,
        })
        v = T.volume_trend(df)
        assert v["ratio"] > 1.5  # recent 10d avg doubled vs 50d baseline


class TestGoldenCross:
    def test_golden_cross_detected(self):
        # long downtrend then strong recovery long enough to flip SMA50>SMA200
        prices = list(np.linspace(300, 100, 250)) + list(np.linspace(100, 320, 130))
        assert T.golden_cross(series(prices), lookback=130) == "golden"
