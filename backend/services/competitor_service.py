"""Competitor endpoint — delegates to the L6 layer:

  - peer metric rows ......... app.analytics.competitor_analysis.compare_industry
  - per-metric ranking ....... app.analytics.competitor_analysis.compare_symbol

The only derived value is `overall_rank` (mean of the per-metric ranks),
computed for the frontend's "Rank in Industry" card.
"""

import logging

from app.analytics.competitor_analysis import compare_industry, compare_symbol, get_peers
from backend.core.exceptions import NoDataError, NotFoundError
from backend.schemas.competitor import CompetitorOut, MetricComparison, PeerRow

logger = logging.getLogger("finverse.api")


class CompetitorService:
    def get_competitors(self, symbol: str) -> CompetitorOut:
        symbol = symbol.upper()
        industry, peers = get_peers(symbol)
        if industry is None:
            raise NotFoundError(f"Unknown symbol: {symbol}")
        if not peers:
            raise NoDataError(f"No industry mapping for {symbol}; cannot build a peer group.")

        result = compare_symbol(symbol)
        if "error" in result:
            raise NoDataError(
                f"No analytics available for {symbol} yet ({result['error']}). "
                "Run the price/financials ETL first."
            )

        peer_rows = compare_industry(industry)

        comparison = [
            MetricComparison(
                metric=metric,
                value=c["value"],
                peer_avg=c["peer_avg"],
                rank=c["rank"],
                out_of=c["out_of"],
            )
            for metric, c in result["comparison"].items()
        ]
        ranks = [c.rank for c in comparison if c.rank is not None]
        overall_rank = round(sum(ranks) / len(ranks)) if ranks else None

        return CompetitorOut(
            symbol=symbol,
            company=result.get("company"),
            industry=industry,
            peer_count=result["peer_count"],
            overall_rank=overall_rank,
            peers=[PeerRow(**{k: r.get(k) for k in PeerRow.model_fields}) for r in peer_rows],
            comparison=comparison,
        )


competitor_service = CompetitorService()
