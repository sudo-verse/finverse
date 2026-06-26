"""Saved screener filters + the background screen-alert evaluator.

Filters are stored as the screener UI's field→value map. The server interprets
each field with `_FIELDS` (attribute + kind), identical to the client, so a
saved screen matches the same rows in the browser and on the worker. Screens
flagged `notify` are re-evaluated on the AlertWorker thread; when a stock newly
enters the result set, an AlertEvent (+ Telegram) fires — first run only sets a
baseline.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.database import engine as db_engine, get_session
from app.db.models import AlertEvent, SavedScreen
from backend.schemas.saved_screen import SavedScreenCreate, SavedScreenOut
from backend.schemas.screener import ScreenerRow
from backend.services import screener_service, universe_service

logger = logging.getLogger("finverse.api")

# client field name -> (ScreenerRow attribute, kind). Kind mirrors the UI:
# "max" keeps rows <= value, "min" keeps >= value, "min-pct" divides by 100 first.
_FIELDS: dict[str, tuple[str, str]] = {
    "pe": ("pe", "max"),
    "roe": ("roe", "min-pct"),
    "roce": ("roce", "min-pct"),
    "npm": ("npm", "min-pct"),
    "debtToEquity": ("debt_to_equity", "max"),
    "revenueGrowth": ("revenue_growth", "min-pct"),
    "profitGrowth": ("profit_growth", "min-pct"),
    "sentiment": ("sentiment", "min"),
}


def _ensure_tables() -> None:
    SavedScreen.__table__.create(db_engine, checkfirst=True)


def apply(rows: list[ScreenerRow], filters: dict | None, industry: str | None) -> list[ScreenerRow]:
    """Server-side replica of the screener UI's filtering (used for alerts and
    saved-screen runs)."""
    out = rows
    if industry and industry != "ALL":
        out = [r for r in out if r.industry == industry]
    for field, (attr, kind) in _FIELDS.items():
        raw = (filters or {}).get(field)
        if raw is None or str(raw).strip() == "":
            continue
        try:
            v = float(raw) / (100 if kind == "min-pct" else 1)
        except (TypeError, ValueError):
            continue
        kept = []
        for r in out:
            x = getattr(r, attr, None)
            if x is None:
                continue
            if (x <= v) if kind == "max" else (x >= v):
                kept.append(r)
        out = kept
    return out


def _matches(session: Session, sc: SavedScreen) -> list[ScreenerRow]:
    base = universe_service.filter_rows(screener_service.screen(session), sc.universe)
    return apply(base, sc.filters, sc.industry)


class SavedScreenService:
    def list(self, session: Session, user_id: int) -> list[SavedScreenOut]:
        _ensure_tables()
        rows = (session.query(SavedScreen).filter_by(user_id=user_id)
                .order_by(SavedScreen.id.desc()).all())
        return [
            SavedScreenOut(
                id=r.id, name=r.name, filters=r.filters or {}, industry=r.industry,
                universe=r.universe, notify=bool(r.notify),
                last_count=len(r.last_symbols) if r.last_symbols is not None else None,
                created_at=r.created_at,
            )
            for r in rows
        ]

    def create(self, session: Session, user_id: int, payload: SavedScreenCreate) -> SavedScreenOut:
        _ensure_tables()
        # upsert on (user, name) so "Save" over an existing name updates it
        sc = (session.query(SavedScreen)
              .filter_by(user_id=user_id, name=payload.name.strip()).first())
        if sc is None:
            sc = SavedScreen(user_id=user_id, name=payload.name.strip())
            session.add(sc)
        sc.filters = payload.filters or {}
        sc.industry = payload.industry
        sc.universe = payload.universe
        sc.notify = payload.notify
        # baseline the current matches so a notify screen doesn't fire for
        # everything already matching at save time.
        try:
            sc.last_symbols = sorted(r.symbol for r in _matches(session, sc))
        except Exception:
            sc.last_symbols = []
        sc.last_run_at = datetime.utcnow()
        session.commit()
        session.refresh(sc)
        return SavedScreenOut(
            id=sc.id, name=sc.name, filters=sc.filters or {}, industry=sc.industry,
            universe=sc.universe, notify=bool(sc.notify),
            last_count=len(sc.last_symbols or []), created_at=sc.created_at,
        )

    def delete(self, session: Session, user_id: int, screen_id: int) -> None:
        _ensure_tables()
        session.query(SavedScreen).filter_by(user_id=user_id, id=screen_id).delete()
        session.commit()

    # ------------------------------------------------------------- evaluator
    def evaluate_notifies(self) -> int:
        """Re-run every notify screen; fire on new entrants. Owns its session,
        never raises. Returns #fired."""
        _ensure_tables()
        fired = 0
        with get_session() as s:
            screens = s.query(SavedScreen).filter_by(notify=True).all()
            if not screens:
                return 0
            base = screener_service.screen(s)
            uni_cache: dict[str | None, list[ScreenerRow]] = {}
            for sc in screens:
                rows = uni_cache.get(sc.universe)
                if rows is None:
                    rows = universe_service.filter_rows(base, sc.universe)
                    uni_cache[sc.universe] = rows
                syms = sorted(r.symbol for r in apply(rows, sc.filters, sc.industry))
                prev = set(sc.last_symbols or [])
                new = [x for x in syms if x not in prev]
                # only alert once a baseline exists (avoid firing on first run)
                if sc.last_symbols is not None and new:
                    shown = ", ".join(new[:8]) + ("…" if len(new) > 8 else "")
                    msg = f"{len(new)} new in screen '{sc.name}': {shown}"
                    s.add(AlertEvent(user_id=sc.user_id, rule_id=None, symbol=new[0], message=msg))
                    fired += 1
                    try:
                        from app.utils.telegram import send_telegram

                        send_telegram(f"🔎 Finverse screen alert — {sc.name}\n{msg}")
                    except Exception:
                        pass
                sc.last_symbols = syms
                sc.last_run_at = datetime.utcnow()
        if fired:
            logger.info("screen-alerts: fired %d", fired)
        return fired


saved_screen_service = SavedScreenService()
