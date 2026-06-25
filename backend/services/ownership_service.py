"""Ownership / shareholding-activity analytics over the persisted snapshots.

Market-wide "who's accumulating / reducing" view for promoter, FII and DII
holdings, derived by comparing each company's two most recent quarterly
snapshots of the chosen metric.
"""

from sqlalchemy.orm import Session

from app.db.models import Company, Shareholding
from backend.schemas.ownership import OwnershipActivityRow, OwnershipHistoryRow

_COL = {
    "promoter": Shareholding.promoter_pct,
    "fii": Shareholding.fii_pct,
    "dii": Shareholding.dii_pct,
    "mf": Shareholding.mf_pct,
    "insurance": Shareholding.insurance_pct,
    "banks": Shareholding.banks_pct,
    "pension": Shareholding.pension_pct,
}


class OwnershipService:
    def activity(self, session: Session, metric: str = "promoter", direction: str = "buying",
                 limit: int = 50, min_change: float = 0.05) -> list[OwnershipActivityRow]:
        """Stocks ranked by QoQ change in the chosen holding metric.

        metric: promoter | fii | dii. direction="buying" → biggest increases,
        "selling" → biggest decreases. Only companies with two consecutive
        non-null snapshots of the metric are considered.
        """
        col = _COL.get(metric)
        if col is None:
            return []

        rows = (
            session.query(Shareholding.company_id, Company.symbol, Company.name,
                          Shareholding.period, col.label("pct"))
            .join(Company, Company.id == Shareholding.company_id)
            .filter(col.isnot(None))
            .order_by(Shareholding.company_id, Shareholding.period_date.desc())
            .all()
        )

        by_co: dict[int, dict] = {}
        for cid, sym, name, period, pct in rows:
            co = by_co.setdefault(cid, {"sym": sym, "name": name, "snaps": []})
            co["snaps"].append((period, pct))

        out: list[OwnershipActivityRow] = []
        for co in by_co.values():
            snaps = co["snaps"]  # newest first
            if len(snaps) < 2:
                continue
            (lp, lpct), (pp, ppct) = snaps[0], snaps[1]
            if lpct is None or ppct is None:
                continue
            out.append(OwnershipActivityRow(
                symbol=co["sym"], name=co["name"], metric=metric,
                pct=lpct, prev_pct=ppct, change=round(lpct - ppct, 2),
                period=lp, prev_period=pp,
            ))

        if direction == "selling":
            out = [r for r in out if r.change is not None and r.change <= -min_change]
            out.sort(key=lambda r: r.change)
        else:
            out = [r for r in out if r.change is not None and r.change >= min_change]
            out.sort(key=lambda r: r.change, reverse=True)
        return out[:limit]

    def history(self, session: Session, symbol: str, limit: int = 8) -> list[OwnershipHistoryRow]:
        """Quarterly ownership snapshots for one stock, oldest→newest (for trend
        charts). Includes the FII/DII aggregates and the DII sub-categories."""
        company = session.query(Company).filter(Company.symbol == symbol.upper()).first()
        if company is None:
            return []
        rows = (
            session.query(Shareholding)
            .filter(Shareholding.company_id == company.id)
            .order_by(Shareholding.period_date.desc())
            .limit(limit)
            .all()
        )
        out = [
            OwnershipHistoryRow(
                period=r.period, promoter=r.promoter_pct, public=r.public_pct,
                fii=r.fii_pct, dii=r.dii_pct, mf=r.mf_pct, insurance=r.insurance_pct,
                banks=r.banks_pct, pension=r.pension_pct,
            )
            for r in rows
        ]
        out.reverse()  # chronological for charting
        return out


ownership_service = OwnershipService()
