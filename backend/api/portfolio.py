from fastapi import APIRouter, status

from backend.schemas.portfolio import HoldingCreate, PortfolioOut
from backend.services.portfolio_service import portfolio_service

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio", response_model=PortfolioOut, summary="Portfolio analytics")
def get_portfolio() -> PortfolioOut:
    """Holdings with valuation/P&L, total value, day P&L, allocation weights,
    sector allocation, concentration (HHI) and risk metrics (volatility,
    annualized return, Sharpe)."""
    return portfolio_service.get_portfolio()


@router.post(
    "/portfolio/holdings",
    status_code=status.HTTP_201_CREATED,
    summary="Add or top-up a holding",
)
def add_holding(payload: HoldingCreate) -> dict[str, str]:
    """Adds a position; if the symbol already exists, quantity accumulates and
    the average price is blended (existing repository behaviour)."""
    portfolio_service.add(payload)
    return {"status": "ok", "symbol": payload.symbol.upper()}


@router.delete(
    "/portfolio/holdings",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear all holdings",
)
def clear_holdings() -> None:
    portfolio_service.clear()
