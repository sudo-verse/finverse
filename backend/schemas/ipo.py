"""Schema for the IPO / SME-IPO tracker (NSE primary-market feeds)."""

from backend.schemas.common import APIModel


class IpoRow(APIModel):
    symbol: str | None = None
    name: str
    category: str | None = None       # Mainboard | SME
    status: str | None = None         # open | upcoming | listed
    price_band: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    issue_size: str | None = None
    open_date: str | None = None
    close_date: str | None = None
    listing_date: str | None = None
    subscription: float | None = None  # times subscribed (x)
