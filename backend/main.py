"""Finverse API — FastAPI layer over the existing analytics/genai engine.

Run:  uvicorn backend.main:app --reload --port 8000 --reload-dir app --reload-dir backend --reload-include '*.py'
      (scoped reload dirs: the embedded news engine writes signals.json /
      finverse.db in the repo root — watching them would restart the server
      on every ingested article)
Docs: http://localhost:8000/docs  (OpenAPI JSON at /openapi.json)

Endpoints are defined as sync `def`s on purpose: the underlying stack
(SQLAlchemy ORM, pandas, Gemini SDK, ChromaDB) is blocking, so FastAPI runs
each request on its threadpool instead of blocking the event loop.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import (
    chat,
    competitors,
    dashboard,
    market,
    portfolio,
    reports,
    research,
    screener,
    sentiment,
    signals,
    stocks,
    watchlist,
)
from backend.core.config import settings
from backend.core.exceptions import NoDataError, NotFoundError, ServiceUnavailableError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("finverse.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables on first run so a fresh checkout works out of the box
    # (same bootstrap the Streamlit app used).
    from app.db.init_db import init_db

    init_db()
    logger.info("Finverse API started (db ready, CORS: %s)", settings.cors_origin_list)

    # Embedded real-time news engine — keeps signals fresh without a
    # separate `python -m app.main_nse` process.
    from backend.core.engine import (
        start_alerts,
        start_engine,
        start_etl,
        stop_alerts,
        stop_engine,
        stop_etl,
    )

    if settings.engine_enabled:
        start_engine(settings.engine_interval)
    if settings.etl_enabled:
        start_etl(settings.etl_hour_ist, settings.etl_minute_ist)
    start_alerts(settings.alerts_interval)
    yield
    stop_alerts()
    stop_etl()
    stop_engine()
    logger.info("Finverse API shutting down")


app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Request logging
# --------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %d (%.1f ms)",
        request.method, request.url.path, response.status_code, duration_ms,
    )
    return response


# --------------------------------------------------------------------------
# Domain exception -> HTTP mapping
# --------------------------------------------------------------------------
@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(NoDataError)
async def no_data_handler(_: Request, exc: NoDataError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ServiceUnavailableError)
async def unavailable_handler(_: Request, exc: ServiceUnavailableError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/health", tags=["meta"], summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.version}


@app.get("/api/engine/status", tags=["meta"], summary="Embedded news-engine status")
async def engine_status() -> dict:
    from backend.core.engine import engine_worker, etl_worker

    news = {"enabled": settings.engine_enabled, **(engine_worker.status if engine_worker else {"running": False})}
    etl = {"enabled": settings.etl_enabled, **(etl_worker.status if etl_worker else {"running": False})}
    return {**news, "etl": etl}


# Serve the research document corpus so source citations can open the
# original filing (/docfiles/<SYMBOL>/<doc_type>/<file>#page=N).
# NB: mounted at /docfiles, not /documents — the frontend owns the
# /documents route (Document Center page).
import os

from fastapi.staticfiles import StaticFiles

if os.path.isdir("documents"):
    app.mount("/docfiles", StaticFiles(directory="documents"), name="docfiles")


for router in (
    dashboard.router,
    signals.router,
    stocks.router,
    competitors.router,
    portfolio.router,
    market.router,
    reports.router,
    chat.router,
    research.router,
    screener.router,
    sentiment.router,
    watchlist.router,
):
    app.include_router(router, prefix=settings.api_prefix)
