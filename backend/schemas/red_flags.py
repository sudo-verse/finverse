"""Schemas for the stock red-flags panel and the market surveillance feed."""

from backend.schemas.common import APIModel


class RedFlag(APIModel):
    label: str
    detail: str | None = None
    severity: str             # high | medium | low | info


class RedFlagsOut(APIModel):
    symbol: str
    asm: str | None = None
    gsm: str | None = None
    surveillance_desc: str | None = None
    pledged_pct: float | None = None          # % of promoter shares pledged
    promoter_holding_pct: float | None = None
    leverage: float | None = None             # total liabilities / total assets
    equity_ratio: float | None = None         # total equity / total assets
    stress: str | None = None                 # low | elevated | high
    flags: list[RedFlag] = []


class SurveillanceRow(APIModel):
    symbol: str
    name: str | None = None
    asm: str | None = None
    gsm: str | None = None
    desc: str | None = None
