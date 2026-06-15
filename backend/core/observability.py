"""Observability: request-id correlation, structured logging, optional Sentry.

Every request gets an id (from an inbound `X-Request-ID` or freshly minted) that
is attached to every log line emitted while handling it and echoed back in the
response header — so a user-reported error maps to a precise log trace.
"""

import logging
import uuid
from contextvars import ContextVar

from backend.core.config import settings

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

LOG_FORMAT = "%(asctime)s [%(request_id)s] %(name)s %(levelname)s %(message)s"


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def configure_logging() -> None:
    """Install the request-id filter + format on the root logger's handlers."""
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    filt = _RequestIdFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(filt)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))


def new_request_id(inbound: str | None) -> str:
    rid = (inbound or "").strip()[:64] or uuid.uuid4().hex[:16]
    request_id_ctx.set(rid)
    return rid


def init_sentry() -> bool:
    """Initialise Sentry if a DSN is configured and the SDK is installed.
    Returns True if enabled."""
    if not settings.sentry_dsn:
        return False
    try:
        import sentry_sdk
    except ImportError:
        logging.getLogger("finverse.api").warning(
            "SENTRY_DSN set but sentry-sdk is not installed; skipping."
        )
        return False
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.version,
        traces_sample_rate=0.1,
    )
    return True
