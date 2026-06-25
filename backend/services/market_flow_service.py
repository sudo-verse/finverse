"""Read-side analytics over the persisted daily FII/DII market flows."""

from sqlalchemy.orm import Session

from app.db.models import MarketFlow
from backend.schemas.market_flow import MarketFlowRow, MarketFlowSummary


class MarketFlowService:
    def summary(self, session: Session, days: int = 30) -> MarketFlowSummary:
        """Latest snapshot + the last `days` trading days + rolling net totals."""
        rows = (
            session.query(MarketFlow)
            .order_by(MarketFlow.date.desc())
            .limit(days)
            .all()
        )
        if not rows:
            return MarketFlowSummary(window_days=days)

        rows.reverse()  # chronological for charting
        history = [
            MarketFlowRow(
                date=r.date,
                fii_buy=r.fii_buy, fii_sell=r.fii_sell, fii_net=r.fii_net,
                dii_buy=r.dii_buy, dii_sell=r.dii_sell, dii_net=r.dii_net,
            )
            for r in rows
        ]
        fii_sum = sum(r.fii_net for r in rows if r.fii_net is not None)
        dii_sum = sum(r.dii_net for r in rows if r.dii_net is not None)
        return MarketFlowSummary(
            latest=history[-1],
            history=history,
            fii_net_window=round(fii_sum, 2),
            dii_net_window=round(dii_sum, 2),
            window_days=len(history),
        )


market_flow_service = MarketFlowService()
