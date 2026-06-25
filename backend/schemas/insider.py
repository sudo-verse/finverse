"""Schemas for insider (SEBI PIT) and substantial-acquisition (SAST) disclosures.

Market-wide insider/PIT is no longer served by NSE (returns empty), so the
market feed is built on SAST Reg29 filings (acquirers/promoters crossing
disclosure thresholds); per-stock insider trades use the still-working
per-symbol corporates-pit endpoint.
"""

from backend.schemas.common import APIModel


class SastRow(APIModel):
    """One SAST Reg29 substantial-acquisition / sale disclosure."""
    symbol: str | None = None
    company: str | None = None
    acquirer: str | None = None
    action: str | None = None          # "Acquisition" | "Sale"
    is_promoter: bool = False
    shares: int | None = None          # shares acquired or sold
    pct_traded: float | None = None    # % of capital in this transaction
    pct_after: float | None = None     # holding % after the transaction
    mode: str | None = None            # market / off-market / others
    reg_type: str | None = None        # Reg29(1) / Reg29(2)
    trade_date: str | None = None      # NSE's acquirerDate range string
    filed_at: str | None = None        # ISO-ish filing timestamp
    attachment_url: str | None = None


class InsiderTrade(APIModel):
    """One SEBI PIT insider trade for a single company."""
    symbol: str | None = None
    person: str | None = None
    person_category: str | None = None   # Promoter / Director / KMP / …
    transaction_type: str | None = None  # Buy / Sell / Pledge / …
    security_type: str | None = None
    quantity: int | None = None
    value: float | None = None
    pct_before: float | None = None
    pct_after: float | None = None
    mode: str | None = None
    trade_date: str | None = None
    filed_at: str | None = None
