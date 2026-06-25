"""Embedded news-ingestion worker.

Runs the existing real-time engine (app.main_nse.run_cycle — fetch news from
all sources, FinBERT sentiment, event classification, signal generation,
DB persistence) on a background thread inside the API process, so the
website stays live without a separate `python -m app.main_nse` terminal.

Disable with BACKEND_ENGINE_ENABLED=false (e.g. when running the standalone
engine elsewhere); tune the sweep cadence with BACKEND_ENGINE_INTERVAL.
Both processes can coexist safely — dedup is by unique `uid` in the DB and
the shared engine_state.json seen-set.
"""

import logging
import threading
from datetime import datetime, timezone

logger = logging.getLogger("finverse.api")


class EngineWorker:
    def __init__(self, interval_seconds: int):
        self.interval = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.status: dict = {
            "running": False,
            "interval_seconds": interval_seconds,
            "sweeps": 0,
            "last_sweep_at": None,
            "last_new_signals": 0,
            "total_new_signals": 0,
            "last_error": None,
        }

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="finverse-engine", daemon=True
        )
        self._thread.start()
        self.status["running"] = True
        logger.info("engine: ingestion worker started (every %ss)", self.interval)

    def stop(self) -> None:
        self._stop.set()
        self.status["running"] = False

    def _loop(self) -> None:
        # Imports deferred to the worker thread: the first sweep lazily loads
        # FinBERT, which must not delay API startup.
        from app.ingestion.unified_fetcher import UnifiedFetcher
        from app.main_nse import load_seen_uids, run_cycle

        fetcher = UnifiedFetcher()
        seen_uids = load_seen_uids()
        seen_set = set(seen_uids)

        while not self._stop.is_set():
            try:
                new = run_cycle(fetcher, seen_uids, seen_set)
                self.status.update(
                    last_sweep_at=datetime.now(timezone.utc).isoformat(),
                    last_new_signals=new,
                    sweeps=self.status["sweeps"] + 1,
                    total_new_signals=self.status["total_new_signals"] + new,
                    last_error=None,
                )
                if new:
                    logger.info("engine: %d new signals ingested", new)
            except Exception as e:  # one bad sweep must not kill the worker
                self.status["last_error"] = str(e)
                logger.exception("engine: sweep failed")
            self._stop.wait(self.interval)


engine_worker: EngineWorker | None = None


def start_engine(interval_seconds: int) -> EngineWorker:
    global engine_worker
    if engine_worker is None:
        engine_worker = EngineWorker(interval_seconds)
    engine_worker.start()
    return engine_worker


def stop_engine() -> None:
    if engine_worker is not None:
        engine_worker.stop()


class EtlWorker:
    """Daily data refresh on a background thread.

    - prices_etl (1mo top-up, upserts) every day at the configured IST time
    - companies_etl + financials_etl weekly (Sunday) — fundamentals move
      quarterly, no point hammering Yahoo daily
    - catch-up on startup: if the newest price bar is older than a day,
      run immediately instead of waiting for the schedule
    """

    IST_OFFSET = 5.5 * 3600

    def __init__(self, hour_ist: int, minute_ist: int):
        self.hour, self.minute = hour_ist, minute_ist
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.status: dict = {"running": False, "runs": 0, "last_run_at": None,
                             "next_run_at": None, "last_error": None}

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="finverse-etl", daemon=True)
        self._thread.start()
        self.status["running"] = True
        logger.info("etl: daily refresh scheduled for %02d:%02d IST", self.hour, self.minute)

    def stop(self) -> None:
        self._stop.set()
        self.status["running"] = False

    def _seconds_until_next_run(self) -> float:
        import time as _time

        now_ist = _time.time() + self.IST_OFFSET
        day = 86400
        today_run = (now_ist // day) * day + self.hour * 3600 + self.minute * 60
        if today_run <= now_ist:
            today_run += day
        return today_run - now_ist

    @staticmethod
    def _prices_stale() -> bool:
        from datetime import date, timedelta

        from sqlalchemy import func

        from app.db.database import get_session
        from app.db.models import PriceHistory

        try:
            with get_session() as s:
                newest = s.query(func.max(PriceHistory.date)).scalar()
            return newest is None or newest < date.today() - timedelta(days=1)
        except Exception:
            return False

    def _run_once(self) -> None:
        from datetime import datetime, timezone

        from app.etl import companies_etl, deals_etl, financials_etl, market_flow_etl, prices_etl

        weekly = datetime.now(timezone.utc).weekday() == 6  # Sunday
        if weekly:
            companies_etl.run()
        prices_etl.run(period="1mo")
        if weekly:
            financials_etl.run()
        for name, fn in (("market-flow", market_flow_etl.run), ("deals", deals_etl.run)):
            try:
                fn()  # daily FII/DII flows + bulk/block deals
            except Exception as e:
                logger.warning("etl: %s refresh failed: %s", name, e)
        self._snapshot_sentiment()
        self.status.update(
            runs=self.status["runs"] + 1,
            last_run_at=datetime.now(timezone.utc).isoformat(),
            last_error=None,
        )
        logger.info("etl: daily refresh complete (weekly=%s)", weekly)

    @staticmethod
    def _snapshot_sentiment() -> None:
        """Daily sentiment snapshot for tracked symbols (watchlist + holdings)
        so the history chart builds without anyone visiting the page."""
        from app.db.database import get_session
        from app.db.models import PortfolioHolding, WatchlistItem
        from backend.services.sentiment_service import sentiment_service

        with get_session() as s:
            symbols = {r.symbol for r in s.query(WatchlistItem.symbol).all()}
            symbols |= {r.symbol for r in s.query(PortfolioHolding.symbol).all()}
        for symbol in sorted(symbols):
            try:
                with get_session() as s:
                    sentiment_service.compute(s, symbol, force=True)  # persists snapshot
            except Exception as e:
                logger.warning("etl: sentiment snapshot failed for %s: %s", symbol, e)
        if symbols:
            logger.info("etl: sentiment snapshots saved for %d tracked symbols", len(symbols))

        # Universe-wide pass so the sentiment leaderboard (and the AI assistant's
        # "top stocks by sentiment" answers) cover the whole NSE list, not just
        # tracked names. Skips the per-symbol NSE ownership call to stay fast.
        try:
            stats = sentiment_service.refresh_universe()
            logger.info("etl: sentiment universe refresh %s", stats)
        except Exception as e:
            logger.warning("etl: sentiment universe refresh failed: %s", e)

    def _loop(self) -> None:
        from datetime import datetime, timedelta, timezone

        # catch-up after downtime, but give the API a moment to settle first
        if self._stop.wait(30):
            return
        if self._prices_stale():
            try:
                logger.info("etl: price data is stale — running catch-up refresh")
                self._run_once()
            except Exception as e:
                self.status["last_error"] = str(e)
                logger.exception("etl: catch-up failed")

        while not self._stop.is_set():
            wait = self._seconds_until_next_run()
            self.status["next_run_at"] = (
                datetime.now(timezone.utc) + timedelta(seconds=wait)
            ).isoformat()
            if self._stop.wait(wait):
                return
            try:
                self._run_once()
            except Exception as e:  # one bad day must not kill the schedule
                self.status["last_error"] = str(e)
                logger.exception("etl: daily refresh failed")


etl_worker: EtlWorker | None = None


def start_etl(hour_ist: int, minute_ist: int) -> EtlWorker:
    global etl_worker
    if etl_worker is None:
        etl_worker = EtlWorker(hour_ist, minute_ist)
    etl_worker.start()
    return etl_worker


def stop_etl() -> None:
    if etl_worker is not None:
        etl_worker.stop()


class AlertWorker:
    """Evaluates alert rules every few minutes (separate from the news sweep
    so a slow NSE call can't starve ingestion)."""

    def __init__(self, interval_seconds: int):
        self.interval = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.status: dict = {"running": False, "checks": 0, "fired_total": 0, "last_error": None}

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="finverse-alerts", daemon=True)
        self._thread.start()
        self.status["running"] = True
        logger.info("alerts: evaluator started (every %ss)", self.interval)

    def stop(self) -> None:
        self._stop.set()
        self.status["running"] = False

    def _loop(self) -> None:
        from backend.services.watchlist_service import watchlist_service

        while not self._stop.is_set():
            if self._stop.wait(self.interval):
                return
            try:
                fired = watchlist_service.evaluate_all()
                self.status.update(checks=self.status["checks"] + 1,
                                   fired_total=self.status["fired_total"] + fired,
                                   last_error=None)
            except Exception as e:
                self.status["last_error"] = str(e)
                logger.exception("alerts: evaluation cycle failed")


alert_worker: AlertWorker | None = None


def start_alerts(interval_seconds: int) -> AlertWorker:
    global alert_worker
    if alert_worker is None:
        alert_worker = AlertWorker(interval_seconds)
    alert_worker.start()
    return alert_worker


def stop_alerts() -> None:
    if alert_worker is not None:
        alert_worker.stop()
