"""Schemas for the relative fair-value model.

Fair value is estimated from sector-relative, quality-adjusted multiples
(P/E justified by growth, P/B justified by ROE) — NOT a precise DCF, which our
filing-level cash-flow/shares data can't support reliably. Treated as a
screening signal, not a price target; confidence is surfaced explicitly.
"""

from backend.schemas.common import APIModel


class ValuationOut(APIModel):
    symbol: str
    name: str
    sector: str | None = None
    price: float | None = None
    fair_value: float | None = None
    upside_pct: float | None = None          # (fair - price) / price
    margin_of_safety: float | None = None    # (fair - price) / fair, ≥0 only
    verdict: str | None = None               # undervalued | fairly valued | overvalued
    confidence: str | None = None            # high | medium | low

    pe: float | None = None
    sector_pe: float | None = None
    fair_pe: float | None = None             # quality-adjusted fair multiple
    pe_fair_value: float | None = None

    pb: float | None = None
    sector_pb: float | None = None
    fair_pb: float | None = None
    pb_fair_value: float | None = None

    method: str | None = None
    note: str | None = None


class ValuationRow(APIModel):
    symbol: str
    name: str
    sector: str | None = None
    price: float | None = None
    fair_value: float | None = None
    upside_pct: float | None = None
    verdict: str | None = None
    confidence: str | None = None
