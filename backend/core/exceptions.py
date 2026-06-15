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
