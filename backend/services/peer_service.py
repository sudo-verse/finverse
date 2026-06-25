"""Peer comparison — rank a stock against its sector/industry peers.

Reuses the screener's cached per-company rows (same ratios, same data caveats),
so this adds no new computation or data dependency.
"""

from sqlalchemy.orm import Session

from backend.schemas.peers import PeerComparison, PeerRow
from backend.services import screener_service

_MIN_PEERS = 4  # if an industry is too thin, widen to the whole sector


def _to_row(r, target_symbol: str) -> PeerRow:
    return PeerRow(
        symbol=r.symbol, name=r.name, is_target=(r.symbol == target_symbol),
        price=r.price, market_cap=r.market_cap, pe=r.pe, pb=r.pb, roe=r.roe,
        npm=r.npm, revenue_growth=r.revenue_growth, profit_growth=r.profit_growth,
    )


class PeerService:
    def peers(self, session: Session, symbol: str, limit: int = 8) -> PeerComparison:
        symbol = symbol.upper()
        rows = screener_service.screen(session)
        target = next((r for r in rows if r.symbol == symbol), None)
        if target is None:
            return PeerComparison(symbol=symbol)

        # Prefer same industry; widen to sector if the industry group is thin.
        grouped_by, key = "industry", target.industry
        group = [r for r in rows if r.industry and r.industry == key] if key else []
        if len(group) < _MIN_PEERS and target.sector:
            grouped_by, key = "sector", target.sector
            group = [r for r in rows if (r.sector or r.industry) == key]
        if target not in group:
            group.append(target)

        # Rank by market cap (biggest peers first); always keep the target.
        group.sort(key=lambda r: (r.market_cap or 0), reverse=True)
        top = group[:limit]
        if target not in top:
            top = top[: limit - 1] + [target]
            top.sort(key=lambda r: (r.market_cap or 0), reverse=True)

        return PeerComparison(
            symbol=symbol, group=key, grouped_by=grouped_by,
            peers=[_to_row(r, symbol) for r in top],
        )


peer_service = PeerService()
