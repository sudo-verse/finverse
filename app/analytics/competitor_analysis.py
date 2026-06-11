"""L6 — Competitor analysis: compare a stock against its industry peers.

Combines the fundamental ratios (L5) and quantitative metrics (L4), then ranks
the target stock within its peer group on each metric.
"""

from app.analytics.analytics import analyze_symbol as quant_analyze
from app.analytics.financial_analysis import analyze_symbol as fin_analyze
from app.db.database import get_session
from app.db.models import Company

# Metrics pulled from each layer for the comparison
FIN_METRICS = [
    "revenue_growth", "earnings_growth", "net_profit_margin",
    "roe", "roce", "debt_to_equity", "pe_ratio", "pb_ratio",
]
QUANT_METRICS = ["cumulative_return", "annualized_volatility", "sharpe_ratio"]

# For ranking: True = higher is better, False = lower is better
HIGHER_IS_BETTER = {
    "revenue_growth": True, "earnings_growth": True, "net_profit_margin": True,
    "roe": True, "roce": True, "cumulative_return": True, "sharpe_ratio": True,
    "debt_to_equity": False, "pe_ratio": False, "pb_ratio": False,
    "annualized_volatility": False,
}


def get_peers(symbol: str):
    """Return all symbols in the same industry as `symbol` (including itself)."""
    with get_session() as session:
        company = session.query(Company).filter_by(symbol=symbol).first()
        if not company or not company.industry:
            return company.industry if company else None, []
        peers = (
            session.query(Company.symbol)
            .filter(Company.industry == company.industry)
            .order_by(Company.symbol)
            .all()
        )
        return company.industry, [p for (p,) in peers]


def metrics_for(symbol: str) -> dict:
    """Flatten L4 + L5 metrics for one symbol into a single row."""
    row = {"symbol": symbol}
    fin = fin_analyze(symbol)
    quant = quant_analyze(symbol)
    if "error" not in fin:
        row["company"] = fin.get("company")
        row.update({k: fin.get(k) for k in FIN_METRICS})
    if "error" not in quant:
        row.update({k: quant.get(k) for k in QUANT_METRICS})
    return row


def compare_industry(industry: str) -> list:
    """Return the metric rows for every company in an industry that has data."""
    with get_session() as session:
        symbols = [
            s for (s,) in session.query(Company.symbol)
            .filter(Company.industry == industry)
            .order_by(Company.symbol).all()
        ]
    rows = [metrics_for(s) for s in symbols]
    # keep only rows that actually have some metric data
    return [r for r in rows if any(r.get(m) is not None for m in FIN_METRICS + QUANT_METRICS)]


def _rank(target_value, values, higher_better):
    """1 = best. Returns (rank, n) over the non-null peer values."""
    vals = [v for v in values if v is not None]
    if target_value is None or not vals:
        return None, len(vals)
    ordered = sorted(vals, reverse=higher_better)
    # rank by value (ties share the first matching position)
    return ordered.index(target_value) + 1, len(ordered)


def compare_symbol(symbol: str) -> dict:
    """Compare `symbol` to its industry peers with per-metric rank + peer average."""
    industry, peers = get_peers(symbol)
    if not peers:
        return {"symbol": symbol, "error": "no industry/peers found"}

    rows = [metrics_for(s) for s in peers]
    rows = [r for r in rows if any(r.get(m) is not None for m in FIN_METRICS + QUANT_METRICS)]

    target = next((r for r in rows if r["symbol"] == symbol), None)
    if target is None:
        return {"symbol": symbol, "error": "no data for target symbol"}

    comparison = {}
    for metric in FIN_METRICS + QUANT_METRICS:
        peer_values = [r.get(metric) for r in rows]
        present = [v for v in peer_values if v is not None]
        rank, n = _rank(target.get(metric), peer_values, HIGHER_IS_BETTER.get(metric, True))
        comparison[metric] = {
            "value": target.get(metric),
            "peer_avg": (sum(present) / len(present)) if present else None,
            "rank": rank,
            "out_of": n,
        }

    return {
        "symbol": symbol,
        "company": target.get("company"),
        "industry": industry,
        "peer_count": len(rows),
        "comparison": comparison,
    }
