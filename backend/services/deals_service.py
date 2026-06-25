"""Read-side queries over the persisted bulk/block deals."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.db.models import Deal
from backend.schemas.deals import DealRow


class DealsService:
    def recent(self, session: Session, deal_type: str | None = None, side: str | None = None,
               symbol: str | None = None, days: int = 30, limit: int = 100) -> list[DealRow]:
        """Recent deals, newest first, filterable by type/side/symbol.

        Ranked by value (largest first) within the date window so the biggest
        trades surface, then by recency."""
        q = session.query(Deal).filter(Deal.deal_date >= date.today() - timedelta(days=days))
        if deal_type in ("bulk", "block"):
            q = q.filter(Deal.deal_type == deal_type)
        if side in ("BUY", "SELL"):
            q = q.filter(Deal.side == side)
        if symbol:
            q = q.filter(Deal.symbol == symbol.upper())
        rows = q.order_by(Deal.deal_date.desc(), Deal.value.desc().nullslast()).limit(limit).all()
        return [
            DealRow(
                deal_date=r.deal_date, deal_type=r.deal_type, symbol=r.symbol, name=r.name,
                client_name=r.client_name, side=r.side, quantity=r.quantity,
                price=r.price, value=r.value, remarks=r.remarks,
            )
            for r in rows
        ]


deals_service = DealsService()
