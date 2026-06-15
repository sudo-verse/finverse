"""Tests for auth: password hashing, JWT, and the register/login/me flow
(the isolated TestClient `client` fixture lives in conftest.py)."""

from backend.core import security


class TestPasswordHashing:
    def test_roundtrip(self):
        h = security.hash_password("hunter2pass")
        assert h != "hunter2pass"
        assert security.verify_password("hunter2pass", h)
        assert not security.verify_password("wrong", h)

    def test_verify_handles_garbage(self):
        assert not security.verify_password("x", "not-a-hash")


class TestJWT:
    def test_encode_decode(self):
        tok = security.create_access_token(42, "a@b.com")
        payload = security.decode_access_token(tok)
        assert payload["sub"] == "42" and payload["email"] == "a@b.com"

    def test_tampered_token_rejected(self):
        assert security.decode_access_token("garbage.token.here") is None


class TestAuthFlow:
    def test_register_login_me(self, client):
        r = client.post("/api/auth/register",
                        json={"email": "User@Example.com", "password": "supersecret1",
                              "fullName": "Jane"})
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["tokenType"] == "bearer"
        assert body["user"]["email"] == "user@example.com"  # normalised
        assert body["user"]["plan"] == "free"
        token = body["accessToken"]

        # /me with the token
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "user@example.com"

        # login returns a working token too
        lg = client.post("/api/auth/login",
                         json={"email": "user@example.com", "password": "supersecret1"})
        assert lg.status_code == 200

    def test_duplicate_email_conflict(self, client):
        payload = {"email": "dupe@example.com", "password": "supersecret1"}
        assert client.post("/api/auth/register", json=payload).status_code == 201
        assert client.post("/api/auth/register", json=payload).status_code == 409

    def test_wrong_password_401(self, client):
        client.post("/api/auth/register",
                    json={"email": "x@example.com", "password": "supersecret1"})
        r = client.post("/api/auth/login",
                        json={"email": "x@example.com", "password": "nope"})
        assert r.status_code == 401

    def test_me_requires_auth(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_invalid_email_rejected(self, client):
        r = client.post("/api/auth/register",
                        json={"email": "not-an-email", "password": "supersecret1"})
        assert r.status_code == 422

    def test_short_password_rejected(self, client):
        r = client.post("/api/auth/register",
                        json={"email": "y@example.com", "password": "short"})
        assert r.status_code == 422
