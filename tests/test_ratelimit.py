"""Rate limiting: in-memory limiter logic + auth endpoint brute-force protection."""

from backend.core.ratelimit import InMemoryRateLimiter


class TestInMemoryLimiter:
    def test_allows_up_to_limit_then_blocks(self):
        rl = InMemoryRateLimiter()
        for _ in range(3):
            allowed, retry = rl.hit("k", limit=3, window=60)
            assert allowed and retry == 0
        allowed, retry = rl.hit("k", limit=3, window=60)
        assert not allowed and retry > 0

    def test_keys_are_independent(self):
        rl = InMemoryRateLimiter()
        for _ in range(3):
            rl.hit("a", 3, 60)
        assert rl.hit("b", 3, 60)[0] is True  # different key unaffected


class TestAuthRateLimit:
    def test_login_blocked_after_limit(self, client):
        from backend.core.config import settings

        limit = settings.auth_rate_limit
        body = {"email": "nobody@example.com", "password": "whatever12"}
        # First `limit` attempts pass the limiter (they 401 — no such user).
        for _ in range(limit):
            r = client.post("/api/auth/login", json=body)
            assert r.status_code == 401
        # The next one is rate-limited.
        r = client.post("/api/auth/login", json=body)
        assert r.status_code == 429
        assert "Retry-After" in r.headers
