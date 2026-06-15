from fastapi import APIRouter, Depends, status

from app.db.models import User
from backend.core.deps import get_current_user
from backend.schemas.portfolio import HoldingCreate, PortfolioOut
from backend.services.portfolio_service import portfolio_service

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio", response_model=PortfolioOut, summary="Portfolio analytics")
def get_portfolio(user: User = Depends(get_current_user)) -> PortfolioOut:
    """The signed-in user's holdings with valuation/P&L, total value, day P&L,
    allocation weights, sector allocation, concentration (HHI) and risk metrics
    (volatility, annualized return, Sharpe)."""
    return portfolio_service.get_portfolio(user.id)


@router.post(
    "/portfolio/holdings",
    status_code=status.HTTP_201_CREATED,
    summary="Add or top-up a holding",
)
def add_holding(payload: HoldingCreate, user: User = Depends(get_current_user)) -> dict[str, str]:
    """Adds a position to the user's portfolio; if the symbol already exists,
    quantity accumulates and the average price is blended."""
    portfolio_service.add(user.id, payload)
    return {"status": "ok", "symbol": payload.symbol.upper()}


@router.delete(
    "/portfolio/holdings",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear all holdings",
)
def clear_holdings(user: User = Depends(get_current_user)) -> None:
    portfolio_service.clear(user.id)
