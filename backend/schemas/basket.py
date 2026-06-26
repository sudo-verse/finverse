"""Schema for curated thematic baskets (smallcase-style)."""

from backend.schemas.common import APIModel


class BasketConstituent(APIModel):
    symbol: str
    name: str | None = None
    price: float | None = None
    ret_1m: float | None = None
    ret_3m: float | None = None
    ret_1y: float | None = None


class BasketRow(APIModel):
    key: str
    name: str
    thesis: str
    count: int
    ret_1m: float | None = None
    ret_3m: float | None = None
    ret_1y: float | None = None
    top: list[str] = []


class BasketDetail(BasketRow):
    constituents: list[BasketConstituent] = []
