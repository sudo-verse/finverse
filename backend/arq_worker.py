"""Arq worker — consumes background jobs from Redis.

Run:  arq backend.arq_worker.WorkerSettings
Needs BACKEND_REDIS_URL (the same Redis the API enqueues to).
"""

import logging

from arq.connections import RedisSettings

from backend import tasks
from backend.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def startup(ctx) -> None:
    # Ensure the schema exists (no-op on Alembic-managed Postgres).
    from app.db.init_db import init_db

    init_db()
    logging.getLogger("finverse.worker").info("Arq worker ready")


class WorkerSettings:
    functions = [tasks.refresh_sentiment_universe, tasks.ingest_documents]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(settings.redis_url or "redis://localhost:6379")
    max_jobs = 4              # heavy jobs — keep concurrency modest
    job_timeout = 60 * 60     # an hour for a full reindex/universe refresh
