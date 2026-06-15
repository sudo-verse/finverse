"""Background task functions executed by the Arq worker (backend.arq_worker).

Each is a thin async wrapper that runs the existing (synchronous, heavy) work
off the event loop via asyncio.to_thread, so the same logic powers both the
daily cron and on-demand enqueued jobs. The `ctx` arg is Arq's job context.
"""

import asyncio
import logging

logger = logging.getLogger("finverse.worker")


async def refresh_sentiment_universe(ctx) -> dict:
    """Recompute sentiment for the whole NSE universe (heavy; ~hundreds of
    symbols). Returns {scored, skipped, failed}."""
    from backend.services.sentiment_service import sentiment_service

    logger.info("task: refresh_sentiment_universe starting")
    result = await asyncio.to_thread(sentiment_service.refresh_universe)
    logger.info("task: refresh_sentiment_universe done — %s", result)
    return result


async def ingest_documents(ctx, symbol: str | None = None) -> dict:
    """(Re)index filings into the vector store — whole corpus or one symbol."""
    from app.etl.ingest_documents import ingest_documents as _ingest

    logger.info("task: ingest_documents starting (symbol=%s)", symbol)
    result = await asyncio.to_thread(_ingest, symbol)
    logger.info("task: ingest_documents done — %s", result)
    return result
