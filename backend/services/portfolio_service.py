"""Portfolio endpoints — delegates wholly to the L11 analytics layer
(`app.analytics.portfolio.compute_portfolio`) and the holdings repository.

The only addition is day-P&L, which is presentation glue (last close vs
previous close per holding) rather than new analytics.
"""

import logging

import pandas as pd

from app.analytics.analytics import load_prices
from app.analytics.portfolio import compute_portfolio
from app.db.database import get_session
from app.db.repository import add_holding, clear_holdings, list_holdings
from backend.core.exceptions import NoDataError
from backend.schemas.portfolio import (
    GrowthPoint,
    HoldingCreate,
    HoldingOut,
    MarketCapAllocation,
    PortfolioOut,
    PortfolioSummary,
    SectorAllocation,
)

logger = logging.getLogger("finverse.api")

GROWTH_DAYS = 180

# SEBI-style absolute thresholds in rupees (market cap = price × shares).
_LARGE_CAP = 2.0e11   # ≥ ₹20,000 cr
_MID_CAP = 5.0e10     # ₹5,000–20,000 cr


def _market_cap_allocation(holdings: list[HoldingOut], total_value: float) -> list[MarketCapAllocation]:
    """Split portfolio value across large/mid/small caps, reusing the screener's
    already-computed market caps. Best-effort — never raises."""
    try:
        from backend.services import screener_service

        with get_session() as s:
            caps = {r.symbol: r.market_cap for r in screener_service.screen(s)}
    except Exception:
        logger.warning("portfolio: market-cap allocation unavailable", exc_info=True)
        return []

    buckets = {"Large cap": 0.0, "Mid cap": 0.0, "Small cap": 0.0, "Unknown": 0.0}
    for h in holdings:
        v = h.value or 0.0
        mc = caps.get(h.symbol)
        if mc is None:
            buckets["Unknown"] += v
        elif mc >= _LARGE_CAP:
            buckets["Large cap"] += v
        elif mc >= _MID_CAP:
            buckets["Mid cap"] += v
        else:
            buckets["Small cap"] += v
    rows = [
        MarketCapAllocation(bucket=b, weight=(v / total_value if total_value else 0.0), value=v)
        for b, v in buckets.items() if v > 0
    ]
    rows.sort(key=lambda x: -x.weight)
    return rows


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
    def get_portfolio(self, user_id: int) -> PortfolioOut:
        result = compute_portfolio(user_id)
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
            market_cap_allocation=_market_cap_allocation(holdings, total_value),
            growth=growth,
        )

    def portfolio_value(self, user_id: int) -> tuple[float | None, float | None]:
        """(total_value, day_change_pct) for the dashboard card; never raises."""
        try:
            if not list_holdings(user_id):
                return None, None
            p = self.get_portfolio(user_id)
            return p.summary.total_value, p.summary.day_pnl_pct
        except Exception:  # dashboard must not fail because of portfolio state
            logger.warning("dashboard: portfolio valuation unavailable", exc_info=True)
            return None, None

    def add(self, user_id: int, payload: HoldingCreate) -> None:
        add_holding(user_id, payload.symbol.upper(), payload.quantity, payload.avg_price)
        logger.info("portfolio: user %s added %s x %s", user_id, payload.quantity, payload.symbol)

    def clear(self, user_id: int) -> None:
        clear_holdings(user_id)
        logger.info("portfolio: user %s cleared all holdings", user_id)


portfolio_service = PortfolioService()
