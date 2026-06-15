"""Standalone background-worker process (news engine + daily ETL + alerts).

In a scaled deployment the API runs worker-free (BACKEND_ENGINE_ENABLED=false,
BACKEND_ETL_ENABLED=false, BACKEND_ALERTS_ENABLED=false) and this process owns
the workers — so they run exactly once regardless of how many API replicas
there are.

    python -m backend.worker
"""

import logging
import signal
import threading

from backend.core.config import settings
from backend.core.engine import (
    start_alerts,
    start_engine,
    start_etl,
    stop_alerts,
    stop_engine,
    stop_etl,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("finverse.worker")


def main() -> None:
    from app.db.init_db import init_db

    init_db()  # no-op on Postgres (Alembic-managed); create_all on SQLite dev

    if settings.engine_enabled:
        start_engine(settings.engine_interval)
    if settings.etl_enabled:
        start_etl(settings.etl_hour_ist, settings.etl_minute_ist)
    if settings.alerts_enabled:
        start_alerts(settings.alerts_interval)
    logger.info("Finverse worker started (engine=%s, etl=%s, alerts=%s)",
                settings.engine_enabled, settings.etl_enabled, settings.alerts_enabled)

    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    stop.wait()  # block the main thread; daemon workers run until we exit

    logger.info("Finverse worker shutting down")
    stop_alerts()
    stop_etl()
    stop_engine()


if __name__ == "__main__":
    main()
