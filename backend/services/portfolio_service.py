"""Portfolio endpoints — delegates wholly to the L11 analytics layer
(`app.analytics.portfolio.compute_portfolio`) and the holdings repository.

The only addition is day-P&L, which is presentation glue (last close vs
previous close per holding) rather than new analytics.
"""

import logging

import pandas as pd

from app.analytics.analytics import load_prices
from app.analytics.portfolio import compute_portfolio
from app.db.repository import add_holding, clear_holdings, list_holdings
from backend.core.exceptions import NoDataError
from backend.schemas.portfolio import (
    GrowthPoint,
    HoldingCreate,
    HoldingOut,
    PortfolioOut,
    PortfolioSummary,
    SectorAllocation,
)

logger = logging.getLogger("finverse.api")

GROWTH_DAYS = 180


def _growth_series(
    price_map: dict[str, pd.DataFrame],
    quantities: dict[str, float],
    invested: float | None,
) -> list[GrowthPoint]:
    """Mark-to-market the current holdings over the trailing window.

    Presentation glue only: value_t = sum(qty * close_t) per aligned date.
    """
    closes = pd.DataFrame(
        {
            sym: df["close"]
            for sym, df in price_map.items()
            if df is not None and not df.empty
        }
    )
    if closes.empty:
        return []
    closes = closes.ffill().dropna()
    value = sum(closes[sym] * quantities.get(sym, 0.0) for sym in closes.columns)
    return [
        GrowthPoint(date=idx.date(), value=float(v), invested=invested)
        for idx, v in value.tail(GROWTH_DAYS).items()
    ]


class PortfolioService:
    def get_portfolio(self) -> PortfolioOut:
        result = compute_portfolio()
        if "error" in result:
            raise NoDataError(
                "No holdings in the portfolio yet. Add one via POST /api/portfolio/holdings."
            )

        rows = result["holdings"]
        price_map = {r["symbol"]: load_prices(r["symbol"]) for r in rows}

        holdings: list[HoldingOut] = []
        day_pnl = 0.0
        have_day_data = False
        for r in rows:
            df = price_map.get(r["symbol"])
            day_change_pct = None
            # skip NaN closes (partial trading-day bars from the live feed)
            closes = df["close"].dropna() if df is not None else None
            if closes is not None and len(closes) >= 2 and float(closes.iloc[-2]):
                prev, last = float(closes.iloc[-2]), float(closes.iloc[-1])
                day_change_pct = (last - prev) / prev
                day_pnl += (last - prev) * r["quantity"]
                have_day_data = True
            holdings.append(HoldingOut(**r, day_change_pct=day_change_pct))

        total_value = result["total_value"]
        summary = PortfolioSummary(
            total_value=total_value,
            total_cost=result["total_cost"],
            total_pnl=result["total_pnl"],
            total_pnl_pct=result["total_pnl_pct"],
            day_pnl=day_pnl if have_day_data else None,
            day_pnl_pct=(day_pnl / total_value) if (have_day_data and total_value) else None,
            num_holdings=result["num_holdings"],
            num_sectors=result["num_sectors"],
            hhi=result["hhi"],
            effective_holdings=result["effective_holdings"],
            top_concentration=result["top_concentration"],
            annualized_volatility=result["annualized_volatility"],
            annualized_return=result["annualized_return"],
            sharpe_ratio=result["sharpe_ratio"],
        )

        sector_allocation = [
            SectorAllocation(
                sector=sector,
                weight=weight,
                value=weight * total_value if total_value else None,
            )
            for sector, weight in sorted(
                result["sector_allocation"].items(), key=lambda kv: -kv[1]
            )
        ]
        growth = _growth_series(
            price_map,
            {r["symbol"]: r["quantity"] for r in rows},
            result["total_cost"],
        )
        return PortfolioOut(
            summary=summary,
            holdings=holdings,
            sector_allocation=sector_allocation,
            growth=growth,
        )

    def portfolio_value(self) -> tuple[float | None, float | None]:
        """(total_value, day_change_pct) for the dashboard card; never raises."""
        try:
            if not list_holdings():
                return None, None
            p = self.get_portfolio()
            return p.summary.total_value, p.summary.day_pnl_pct
        except Exception:  # dashboard must not fail because of portfolio state
            logger.warning("dashboard: portfolio valuation unavailable", exc_info=True)
            return None, None

    def add(self, payload: HoldingCreate) -> None:
        add_holding(payload.symbol.upper(), payload.quantity, payload.avg_price)
        logger.info("portfolio: added %s x %s", payload.quantity, payload.symbol)

    def clear(self) -> None:
        clear_holdings()
        logger.info("portfolio: cleared all holdings")


portfolio_service = PortfolioService()
