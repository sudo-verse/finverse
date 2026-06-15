"""Background-job endpoints (/api/jobs) — enqueue heavy work + check status.

Jobs run on the Arq worker (backend.arq_worker). Requires BACKEND_REDIS_URL;
without it these return 503. Enqueue endpoints are auth'd and rate-limited
(these jobs are expensive — admin-gating is a future enhancement).
"""

from fastapi import APIRouter, Depends

from app.db.models import User
from backend.core.deps import get_current_user
from backend.core.queue import enqueue, job_status
from backend.core.ratelimit import rate_limit
from backend.schemas.jobs import IngestJobRequest, JobAccepted

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Heavy maintenance jobs — keep enqueues infrequent per client.
_job_limit = rate_limit(limit=5, window=3600, scope="jobs")


@router.post("/sentiment-refresh", response_model=JobAccepted,
             summary="Enqueue a full-universe sentiment refresh",
             dependencies=[_job_limit])
async def enqueue_sentiment_refresh(_: User = Depends(get_current_user)) -> JobAccepted:
    return JobAccepted(job_id=await enqueue("refresh_sentiment_universe"))


@router.post("/ingest", response_model=JobAccepted,
             summary="Enqueue document (re)ingestion", dependencies=[_job_limit])
async def enqueue_ingest(payload: IngestJobRequest,
                         _: User = Depends(get_current_user)) -> JobAccepted:
    return JobAccepted(job_id=await enqueue("ingest_documents", payload.symbol))


@router.get("/{job_id}", summary="Job status (and result if finished)")
async def get_job(job_id: str, _: User = Depends(get_current_user)) -> dict:
    return await job_status(job_id)
