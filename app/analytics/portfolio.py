"""L11 — Portfolio intelligence: value, P&L, allocation, diversification, risk.

Builds on the price_history table (via the L4 loader) and the company master for
sector allocation. Holdings are stored in the portfolio_holdings table.
"""

import numpy as np
import pandas as pd

from app.analytics import metrics as M
from app.analytics.analytics import load_prices
from app.db.database import get_session
from app.db.models import Company
from app.db.repository import list_holdings


def _latest_close(prices: pd.DataFrame):
    if prices is None or prices.empty:
        return None
    return float(prices["close"].iloc[-1])


def _industries(symbols):
    with get_session() as session:
        rows = (
            session.query(Company.symbol, Company.industry)
            .filter(Company.symbol.in_(symbols))
            .all()
        )
    return {sym: (ind or "Unknown") for sym, ind in rows}


def _returns_frame(price_map: dict) -> pd.DataFrame:
    """Align daily returns of all holdings into one DataFrame (inner join on date)."""
    series = {}
    for sym, prices in price_map.items():
        if prices is not None and not prices.empty and len(prices) > 2:
            series[sym] = prices["close"].pct_change().dropna()
    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series).dropna()


def compute_portfolio(user_id, risk_free=M.DEFAULT_RISK_FREE) -> dict:
    """Compute portfolio-level analytics for one user's stored holdings."""
    holdings = list_holdings(user_id)
    if not holdings:
        return {"error": "no holdings", "holdings": []}

    symbols = [h["symbol"] for h in holdings]
    price_map = {h["symbol"]: load_prices(h["symbol"]) for h in holdings}
    industries = _industries(symbols)

    # --- Per-holding valuation ---
    rows = []
    total_value = 0.0
    total_cost = 0.0
    for h in holdings:
        price = _latest_close(price_map[h["symbol"]])
        qty = h["quantity"]
        value = price * qty if price is not None else None
        cost = h["avg_price"] * qty if h["avg_price"] is not None else None
        pnl = (value - cost) if (value is not None and cost is not None) else None
        pnl_pct = (pnl / cost) if (pnl is not None and cost) else None

        if value is not None:
            total_value += value
        if cost is not None:
            total_cost += cost

        rows.append({
            "symbol": h["symbol"],
            "industry": industries.get(h["symbol"], "Unknown"),
            "quantity": qty,
            "avg_price": h["avg_price"],
            "price": price,
            "value": value,
            "cost": cost,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        })

    # --- Weights & allocation ---
    for r in rows:
        r["weight"] = (r["value"] / total_value) if (r["value"] and total_value) else None

    by_sector = {}
    for r in rows:
        if r["value"]:
            by_sector[r["industry"]] = by_sector.get(r["industry"], 0.0) + r["value"]
    sector_allocation = (
        {k: v / total_value for k, v in by_sector.items()} if total_value else {}
    )

    # --- Diversification ---
    weights = [r["weight"] for r in rows if r["weight"] is not None]
    hhi = float(sum(w ** 2 for w in weights)) if weights else None  # Herfindahl index
    effective_holdings = (1.0 / hhi) if hhi else None
    top_concentration = max(weights) if weights else None

    # --- Risk: portfolio volatility / return / Sharpe from aligned daily returns ---
    returns_df = _returns_frame({r["symbol"]: price_map[r["symbol"]] for r in rows})
    port_vol = port_ret = port_sharpe = None
    if not returns_df.empty:
        # value-weight only the symbols that have return data
        w = np.array([
            next((r["weight"] for r in rows if r["symbol"] == c), 0.0) or 0.0
            for c in returns_df.columns
        ])
        if w.sum() > 0:
            w = w / w.sum()  # renormalize over symbols with data
            port_daily = returns_df.values @ w
            port_vol = float(np.std(port_daily, ddof=1) * np.sqrt(M.TRADING_DAYS))
            port_ret = float(np.mean(port_daily) * M.TRADING_DAYS)
            port_sharpe = (
                (port_ret - risk_free) / port_vol if port_vol else None
            )

    total_pnl = (total_value - total_cost) if total_cost else None
    return {
        "holdings": rows,
        "total_value": total_value,
        "total_cost": total_cost or None,
        "total_pnl": total_pnl,
        "total_pnl_pct": (total_pnl / total_cost) if (total_pnl is not None and total_cost) else None,
        "num_holdings": len(rows),
        "num_sectors": len(sector_allocation),
        "sector_allocation": sector_allocation,
        "hhi": hhi,
        "effective_holdings": effective_holdings,
        "top_concentration": top_concentration,
        "annualized_volatility": port_vol,
        "annualized_return": port_ret,
        "sharpe_ratio": port_sharpe,
    }
