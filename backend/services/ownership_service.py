"""Ownership / shareholding-activity analytics over the persisted snapshots.

Market-wide "promoter accumulating / reducing" view, derived by comparing each
company's two most recent quarterly shareholding snapshots. FII/DII activity
will plug into the same shape once the detailed-filing source is wired.
"""

from sqlalchemy.orm import Session

from app.db.models import Company, Shareholding
from backend.schemas.ownership import PromoterActivityRow


class OwnershipService:
    def promoter_activity(self, session: Session, direction: str = "buying",
                          limit: int = 50, min_change: float = 0.05) -> list[PromoterActivityRow]:
        """Stocks ranked by promoter-holding change between the latest two quarters.

        direction="buying" → biggest increases; "selling" → biggest decreases.
        min_change filters out negligible (rounding-level) moves.
        """
        rows = (
            session.query(Shareholding, Company.symbol, Company.name)
            .join(Company, Company.id == Shareholding.company_id)
            .order_by(Shareholding.company_id, Shareholding.period_date.desc())
            .all()
        )

        by_co: dict[int, dict] = {}
        for shp, sym, name in rows:
            co = by_co.setdefault(shp.company_id, {"sym": sym, "name": name, "snaps": []})
            co["snaps"].append(shp)

        out: list[PromoterActivityRow] = []
        for co in by_co.values():
            snaps = co["snaps"]  # newest first
            if len(snaps) < 2:
                continue
            latest, prev = snaps[0], snaps[1]
            if latest.promoter_pct is None or prev.promoter_pct is None:
                continue
            change = latest.promoter_pct - prev.promoter_pct
            out.append(PromoterActivityRow(
                symbol=co["sym"], name=co["name"],
                promoter_pct=latest.promoter_pct, prev_pct=prev.promoter_pct,
                change=round(change, 2), period=latest.period, prev_period=prev.period,
            ))

        if direction == "selling":
            out = [r for r in out if r.change is not None and r.change <= -min_change]
            out.sort(key=lambda r: r.change)
        else:
            out = [r for r in out if r.change is not None and r.change >= min_change]
            out.sort(key=lambda r: r.change, reverse=True)
        return out[:limit]


ownership_service = OwnershipService()
