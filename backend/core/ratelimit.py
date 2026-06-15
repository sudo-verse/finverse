"""Fixed-window rate limiting with abuse protection.

Backends:
  - InMemory: per-process counters — fine for a single API instance / dev.
  - Redis: shared across replicas (INCR + EXPIRE). Selected when
    BACKEND_REDIS_URL is set; if Redis is unreachable we fall back to in-memory
    so a misconfigured cache can never lock users out of auth.

Use as a FastAPI dependency: `Depends(rate_limit(limit, window, scope))`.
"""

import logging
import threading
import time

from fastapi import Depends, Request

from backend.core.config import settings
from backend.core.exceptions import RateLimitedError

logger = logging.getLogger("finverse.api")


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[int, float]] = {}  # key -> (count, reset_epoch)

    def hit(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            count, reset = self._buckets.get(key, (0, 0.0))
            if now >= reset:
                count, reset = 0, now + window
            count += 1
            self._buckets[key] = (count, reset)
        if count > limit:
            return False, max(1, int(reset - now))
        return True, 0


class RedisRateLimiter:
    def __init__(self, client) -> None:
        self._r = client

    def hit(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        pipe = self._r.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        count, ttl = pipe.execute()
        if count == 1 or ttl < 0:
            self._r.expire(key, window)
            ttl = window
        if count > limit:
            return False, max(1, int(ttl))
        return True, 0


_limiter = None


def get_limiter():
    """Singleton limiter: Redis when configured & reachable, else in-memory."""
    global _limiter
    if _limiter is not None:
        return _limiter
    if settings.redis_url:
        try:
            import redis

            client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            _limiter = RedisRateLimiter(client)
            logger.info("rate limiting: using Redis")
            return _limiter
        except Exception as e:
            logger.warning("rate limiting: Redis unavailable (%s); using in-memory", e)
    _limiter = InMemoryRateLimiter()
    return _limiter


def _client_ip(request: Request) -> str:
    # First hop of X-Forwarded-For (set by the proxy), else the socket peer.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(limit: int, window: int, scope: str):
    """Build a dependency enforcing `limit` requests per `window` seconds per
    client IP, namespaced by `scope`."""
    def _dep(request: Request) -> None:
        key = f"rl:{scope}:{_client_ip(request)}"
        allowed, retry_after = get_limiter().hit(key, limit, window)
        if not allowed:
            raise RateLimitedError(retry_after)
    return Depends(_dep)


def auth_rate_limit():
    """Strict limiter for auth endpoints (brute-force / signup-spam protection)."""
    return rate_limit(settings.auth_rate_limit, settings.auth_rate_window_seconds, "auth")
