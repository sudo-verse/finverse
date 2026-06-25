"""Schema for the bulk/block deals endpoints."""

from datetime import date

from backend.schemas.common import APIModel


class DealRow(APIModel):
    deal_date: date
    deal_type: str                       # "bulk" | "block"
    symbol: str
    name: str | None = None
    client_name: str | None = None
    side: str | None = None              # "BUY" | "SELL"
    quantity: int | None = None
    price: float | None = None
    value: float | None = None           # quantity × price (₹)
    remarks: str | None = None
