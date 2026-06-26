"""Schemas for the composite Conviction Score.

The conviction score fuses the signals we already compute in isolation —
relative valuation, earnings momentum, smart-money (FII/DII) flow, insider/SAST
direction, technical position in the 52-week range and news sentiment — into a
single 0-100 read, with a transparent per-pillar breakdown. It is a screening
synthesis, not advice: every pillar that contributed is surfaced so the score
is never a black box.
"""

from backend.schemas.common import APIModel


class ConvictionPillar(APIModel):
    key: str                       # value | momentum | smart_money | insider | technical | sentiment
    label: str
    score: float | None = None     # 0-100, higher = more bullish; None when no data
    weight: float                  # weight this pillar carried in the blend (0 when absent)
    signal: str                    # up | down | neutral | na
    detail: str | None = None      # short human explanation of the raw input


class ConvictionRow(APIModel):
    symbol: str
    name: str
    sector: str | None = None
    score: float                   # 0-100 composite
    verdict: str                   # high conviction | constructive | neutral | weak
    coverage: int                  # how many pillars had data
    pillars: list[ConvictionPillar] = []
