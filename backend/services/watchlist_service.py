"""Watchlist + alert rules CRUD and the background alert evaluator.

The evaluator runs on the AlertWorker thread (backend.core.engine): for each
active rule it checks the live condition, and on trigger writes an AlertEvent
(in-app bell) and pushes to Telegram. A 24h per-rule cooldown stops repeats.
"""

import logging
from datetime import datetime, timedelta, date

from sqlalchemy.orm import Session

from app.db.database import engine as db_engine, get_session
from app.db.models import AlertEvent, AlertRule, Company, NewsSignal, SentimentScore, WatchlistItem
from backend.core.exceptions import NoDataError, NotFoundError
from backend.schemas.watchlist import (
    ALERT_KINDS,
    AlertEventOut,
    AlertRuleCreate,
    AlertRuleOut,
    WatchlistCreate,
    WatchlistItemOut,
)

logger = logging.getLogger("finverse.api")

COOLDOWN_HOURS = 24


def _ensure_tables() -> None:
    for model in (WatchlistItem, AlertRule, AlertEvent):
        model.__table__.create(db_engine, checkfirst=True)


class WatchlistService:
    # ------------------------------------------------------------- watchlist
    def list(self, session: Session, user_id: int) -> list[WatchlistItemOut]:
        _ensure_tables()
        items = (session.query(WatchlistItem)
                 .filter_by(user_id=user_id)
                 .order_by(WatchlistItem.symbol).all())
        if not items:
            return []
        companies = {
            c.symbol: c for c in
            session.query(Company).filter(Company.symbol.in_([i.symbol for i in items])).all()
        }
        alert_counts = dict(
            session.query(AlertRule.symbol, _count(AlertRule.id))
            .filter(AlertRule.user_id == user_id, AlertRule.active,
                    AlertRule.symbol.in_([i.symbol for i in items]))
            .group_by(AlertRule.symbol).all()
        )
        out = []
        for item in items:
            c = companies.get(item.symbol)
            row = WatchlistItemOut(
                symbol=item.symbol, note=item.note, added_at=item.added_at,
                name=c.name if c else None, industry=c.industry if c else None,
                alert_count=alert_counts.get(item.symbol, 0),
            )
            try:  # live quote is best-effort — never fail the list over NSE
                from backend.services.nse_service import nse_service

                q = nse_service.live_quote(item.symbol)
                row.price, row.change_pct = q.last_price, q.p_change
            except Exception:
                pass
            snap = (
                session.query(SentimentScore)
                .filter_by(symbol=item.symbol)
                .order_by(SentimentScore.date.desc()).first()
            )
            if snap:
                row.sentiment, row.recommendation = snap.overall, snap.recommendation
            out.append(row)
        return out

    def add(self, session: Session, user_id: int, payload: WatchlistCreate) -> None:
        _ensure_tables()
        symbol = payload.symbol.upper()
        if not session.query(Company).filter_by(symbol=symbol).first():
            raise NotFoundError(f"Unknown symbol: {symbol}")
        if not session.query(WatchlistItem).filter_by(user_id=user_id, symbol=symbol).first():
            session.add(WatchlistItem(user_id=user_id, symbol=symbol, note=payload.note))

    def remove(self, session: Session, user_id: int, symbol: str) -> None:
        _ensure_tables()
        symbol = symbol.upper()
        session.query(WatchlistItem).filter_by(user_id=user_id, symbol=symbol).delete()
        # rules are symbol-scoped to the watchlist; clean up this user's too
        session.query(AlertRule).filter_by(user_id=user_id, symbol=symbol).delete()

    def symbols(self) -> "list[str]":  # quoted: `list` method shadows the builtin here
        """Watchlist symbols (own session — used by background workers)."""
        _ensure_tables()
        with get_session() as s:
            return [r.symbol for r in s.query(WatchlistItem.symbol).all()]

    # ----------------------------------------------------------------- rules
    def list_rules(self, session: Session, user_id: int,
                   symbol: str | None = None) -> "list[AlertRuleOut]":
        _ensure_tables()
        q = session.query(AlertRule).filter_by(user_id=user_id).order_by(AlertRule.id.desc())
        if symbol:
            q = q.filter_by(symbol=symbol.upper())
        return [AlertRuleOut.model_validate(r) for r in q.all()]

    def create_rule(self, session: Session, user_id: int,
                    payload: AlertRuleCreate) -> AlertRuleOut:
        _ensure_tables()
        if payload.kind not in ALERT_KINDS:
            raise NoDataError(f"Unknown alert kind — use one of {', '.join(ALERT_KINDS)}.")
        if payload.kind not in ("buy_signal",) and payload.threshold is None:
            raise NoDataError(f"Alert kind '{payload.kind}' needs a threshold.")
        rule = AlertRule(user_id=user_id, symbol=payload.symbol.upper(),
                         kind=payload.kind, threshold=payload.threshold)
        session.add(rule)
        session.flush()
        return AlertRuleOut.model_validate(rule)

    def delete_rule(self, session: Session, user_id: int, rule_id: int) -> None:
        _ensure_tables()
        session.query(AlertRule).filter_by(user_id=user_id, id=rule_id).delete()

    # ---------------------------------------------------------------- events
    def list_events(self, session: Session, user_id: int,
                    limit: int = 30) -> "list[AlertEventOut]":
        _ensure_tables()
        rows = (session.query(AlertEvent).filter_by(user_id=user_id)
                .order_by(AlertEvent.id.desc()).limit(limit).all())
        return [AlertEventOut.model_validate(r) for r in rows]

    def mark_events_seen(self, session: Session, user_id: int) -> None:
        _ensure_tables()
        (session.query(AlertEvent)
         .filter_by(user_id=user_id, seen=False).update({"seen": True}))

    # ------------------------------------------------------------- evaluator
    def evaluate_all(self) -> int:
        """Check every active rule; fire events + Telegram. Returns #fired.
        Runs on a background thread — owns its sessions, never raises."""
        _ensure_tables()
        fired = 0
        with get_session() as s:
            rules = s.query(AlertRule).filter_by(active=True).all()
            cutoff = datetime.utcnow() - timedelta(hours=COOLDOWN_HOURS)
            for rule in rules:
                if rule.last_triggered_at and rule.last_triggered_at > cutoff:
                    continue
                try:
                    message = self._check(s, rule)
                except Exception as e:
                    logger.warning("alerts: rule %s check failed: %s", rule.id, e)
                    continue
                if message:
                    rule.last_triggered_at = datetime.utcnow()
                    s.add(AlertEvent(user_id=rule.user_id, rule_id=rule.id,
                                     symbol=rule.symbol, message=message))
                    fired += 1
                    try:
                        from app.utils.telegram import send_telegram

                        send_telegram(f"🔔 Finverse alert — {rule.symbol}\n{message}")
                    except Exception:
                        pass
        if fired:
            logger.info("alerts: fired %d alert(s)", fired)
        return fired

    def _check(self, session: Session, rule: AlertRule) -> str | None:
        """Returns the alert message if the rule condition holds, else None."""
        kind, t = rule.kind, rule.threshold

        if kind in ("price_above", "price_below"):
            from backend.services.nse_service import nse_service

            price = nse_service.live_quote(rule.symbol).last_price
            if price is None:
                return None
            if kind == "price_above" and price > t:
                return f"Price ₹{price:,.2f} crossed above ₹{t:,.2f}"
            if kind == "price_below" and price < t:
                return f"Price ₹{price:,.2f} dropped below ₹{t:,.2f}"

        elif kind in ("sentiment_above", "sentiment_below"):
            from backend.services.sentiment_service import sentiment_service

            score = sentiment_service.compute(session, rule.symbol).overall
            if kind == "sentiment_above" and score > t:
                return f"Sentiment score {score:.0f} rose above {t:.0f}"
            if kind == "sentiment_below" and score < t:
                return f"Sentiment score {score:.0f} fell below {t:.0f}"

        elif kind == "promoter_change":
            from backend.services.nse_service import nse_service

            periods = nse_service.shareholding(rule.symbol)
            if len(periods) >= 2:
                def promoter(p):
                    return next((h.pct for h in p.holdings if "promoter" in h.category.lower()), None)

                now, prev = promoter(periods[0]), promoter(periods[1])
                if now is not None and prev is not None and abs(now - prev) >= (t or 0.5):
                    direction = "increased" if now > prev else "decreased"
                    return f"Promoter holding {direction} {abs(now - prev):.2f} pp QoQ ({prev:.2f}% → {now:.2f}%)"

        elif kind == "buy_signal":
            recent = (
                session.query(NewsSignal)
                .filter(NewsSignal.ticker == rule.symbol, NewsSignal.signal == "BUY",
                        NewsSignal.created_at >= datetime.combine(date.today(), datetime.min.time()))
                .order_by(NewsSignal.id.desc()).first()
            )
            if recent:
                return f"Engine BUY signal: {(recent.news or '')[:140]}"
        return None


def _count(col):
    from sqlalchemy import func

    return func.count(col)


watchlist_service = WatchlistService()
