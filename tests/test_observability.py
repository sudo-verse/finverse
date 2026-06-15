"""Observability: readiness probe, request-id correlation, security headers."""


class TestProbes:
    def test_health_liveness(self, client):
        r = client.get("/health")
        assert r.status_code == 200 and r.json()["status"] == "ok"

    def test_readyz_checks_db(self, client):
        r = client.get("/readyz")
        assert r.status_code == 200 and r.json()["status"] == "ready"


class TestHeaders:
    def test_request_id_generated_and_returned(self, client):
        r = client.get("/health")
        rid = r.headers.get("X-Request-ID")
        assert rid and len(rid) >= 8

    def test_inbound_request_id_is_echoed(self, client):
        r = client.get("/health", headers={"X-Request-ID": "trace-abc-123"})
        assert r.headers.get("X-Request-ID") == "trace-abc-123"

    def test_security_headers_present(self, client):
        r = client.get("/health")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"
        assert r.headers.get("X-Frame-Options") == "DENY"
        assert r.headers.get("Referrer-Policy") == "no-referrer"
