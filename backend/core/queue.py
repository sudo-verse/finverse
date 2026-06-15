"""Arq job queue access — enqueue background jobs and read their status.

Requires Redis (BACKEND_REDIS_URL); when unset, enqueueing raises
ServiceUnavailableError (the API still runs, jobs are just unavailable). The
Arq worker that consumes these jobs is backend.arq_worker.
"""

import logging

from backend.core.config import settings
from backend.core.exceptions import ServiceUnavailableError

logger = logging.getLogger("finverse.api")

_pool = None


def queue_enabled() -> bool:
    return bool(settings.redis_url)


async def get_pool():
    global _pool
    if not settings.redis_url:
        raise ServiceUnavailableError(
            "Background jobs are not available — set BACKEND_REDIS_URL."
        )
    if _pool is None:
        from arq import create_pool
        from arq.connections import RedisSettings

        _pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    return _pool


async def enqueue(func_name: str, *args, **kwargs) -> str | None:
    """Enqueue a job by registered function name; returns its job id."""
    pool = await get_pool()
    job = await pool.enqueue_job(func_name, *args, **kwargs)
    return job.job_id if job else None


async def job_status(job_id: str) -> dict:
    """Status (and result, if finished) for a job id."""
    from arq.jobs import Job, JobStatus

    pool = await get_pool()
    job = Job(job_id, pool)
    status = await job.status()
    out: dict = {"id": job_id, "status": status.value if isinstance(status, JobStatus) else str(status)}
    if status == JobStatus.complete:
        try:
            out["result"] = await job.result(timeout=1)
        except Exception as e:  # surfaced as a failed job
            out["error"] = str(e)
    return out
