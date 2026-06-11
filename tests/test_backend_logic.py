"""Tests for backend pure logic: scoring bands, growth math, backtest windows."""

from datetime import date

from backend.services.backtest_service import _forward_return
from backend.services.fundamentals_service import _growth
from backend.services.sentiment_service import _band, _clamp, _status


class TestSentimentBands:
    def test_band_edges(self):
        assert _band(85) == "STRONG BUY"
        assert _band(80) == "STRONG BUY"
        assert _band(79.9) == "BUY"
        assert _band(60) == "BUY"
        assert _band(50) == "NEUTRAL"
        assert _band(39.9) == "SELL"
        assert _band(10) == "STRONG SELL"

    def test_status(self):
        assert _status(70) == "bullish"
        assert _status(50) == "neutral"
        assert _status(20) == "bearish"

    def test_clamp(self):
        assert _clamp(-5) == 0.0
        assert _clamp(105) == 100.0
        assert _clamp(50) == 50.0


class TestGrowth:
    def test_normal_growth(self):
        assert _growth(110, 100) == 0.10

    def test_negative_base_is_meaningless(self):
        assert _growth(50, -100) is None

    def test_missing_values(self):
        assert _growth(None, 100) is None
        assert _growth(100, None) is None
        assert _growth(100, 0) is None


class TestForwardReturn:
    def _series(self):
        dates = [date(2026, 1, d) for d in range(1, 31)]
        closes = {d: 100.0 + i for i, d in enumerate(dates)}  # +1/day
        return closes, dates

    def test_seven_day_return(self):
        closes, dates = self._series()
        r = _forward_return(closes, dates, date(2026, 1, 5), 7)
        assert r is not None and r > 0

    def test_signal_after_data_ends(self):
        closes, dates = self._series()
        assert _forward_return(closes, dates, date(2026, 2, 15), 7) is None

    def test_window_too_short_rejected(self):
        # only 2 trading days available after the signal for a 30d horizon
        closes, dates = self._series()
        assert _forward_return(closes, dates, date(2026, 1, 28), 30) is None
