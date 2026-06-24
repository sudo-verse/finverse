"""Schema for the composite stock scorecard (/api/stocks/{symbol}/scorecard)."""

from backend.schemas.common import APIModel


class ScorecardCheck(APIModel):
    category: str                 # "Valuation", "Growth", "Profitability", …
    verdict: str                  # "good" | "average" | "bad" | "na"
    score: int | None = None      # 0 / 50 / 100, or None when not assessable
    detail: str                   # one-line, human-readable reason


class ScorecardOut(APIModel):
    symbol: str
    name: str
    overall_score: int | None = None   # 0-100, avg of assessable checks
    rating: str                        # Strong | Good | Average | Weak | Insufficient data
    checks: list[ScorecardCheck]
