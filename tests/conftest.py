"""Shared fixtures: a TestClient backed by an isolated in-memory-ish SQLite DB
(no engine/ETL workers), plus an auth helper."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BACKEND_ENGINE_ENABLED", "false")
    monkeypatch.setenv("BACKEND_ETL_ENABLED", "false")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import app.db.models  # noqa: F401 — register tables
    from app.db.database import Base
    from app.db.models import Company

    engine = create_engine(f"sqlite:///{tmp_path/'t.db'}",
                            connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    # Seed a company so watchlist/alert validation passes.
    s = TestingSession()
    s.add(Company(symbol="TCS", name="Tata Consultancy Services"))
    s.commit()
    s.close()

    from backend.core.database import get_db
    from backend.main import app

    def _override():
        s = TestingSession()
        try:
            yield s
            s.commit()
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def register(client):
    """Register a user and return Authorization headers for them."""
    def _register(email: str, password: str = "supersecret1") -> dict:
        r = client.post("/api/auth/register", json={"email": email, "password": password})
        assert r.status_code == 201, r.text
        return {"Authorization": f"Bearer {r.json()['accessToken']}"}
    return _register
