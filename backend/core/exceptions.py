"""Domain exceptions raised by services and translated to HTTP responses
by the handlers registered in `backend.main`."""


class NotFoundError(Exception):
    """Requested entity does not exist (→ 404)."""


class NoDataError(Exception):
    """Entity exists but has no underlying data yet (→ 404 with hint)."""


class ServiceUnavailableError(Exception):
    """A required external dependency is not configured/reachable (→ 503)."""


class ConflictError(Exception):
    """Request conflicts with current state, e.g. email already registered (→ 409)."""


class UnauthorizedError(Exception):
    """Authentication missing or invalid (→ 401)."""


class QuotaExceededError(Exception):
    """The caller hit a plan usage limit (→ 429, upsell to upgrade)."""


class RateLimitedError(Exception):
    """Too many requests in a short window (→ 429 with Retry-After)."""

    def __init__(self, retry_after: int, message: str = "Too many requests. Slow down."):
        super().__init__(message)
        self.retry_after = retry_after
