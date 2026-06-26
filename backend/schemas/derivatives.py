"""Schemas for F&O / derivatives analytics (from the NSE EOD FO bhavcopy)."""

from backend.schemas.common import APIModel


class DerivativeRow(APIModel):
    symbol: str
    kind: str                      # Stock | Index
    expiry: str | None = None
    fut_price: float | None = None
    underlying: float | None = None
    oi: float | None = None        # futures open interest (contracts/shares)
    chg_oi_pct: float | None = None
    pcr: float | None = None       # put/call OI ratio (nearest expiry)
    max_pain: float | None = None
    buildup: str | None = None     # Long buildup | Short buildup | Short covering | Long unwinding


class OptionStrike(APIModel):
    strike: float
    ce_oi: float = 0.0
    pe_oi: float = 0.0


class OptionChainOut(APIModel):
    symbol: str
    expiry: str | None = None
    underlying: float | None = None
    pcr: float | None = None
    max_pain: float | None = None
    as_of: str | None = None
    strikes: list[OptionStrike] = []
