"""Plan-based usage metering: limits enforced, cached reports free, /api/usage."""

import pytest

from backend.core.exceptions import QuotaExceededError
from backend.services import usage_service as us_module
from backend.services.usage_service import usage_service


@pytest.fixture(autouse=True)
def _isolate_db(tmp_path, monkeypatch):
    """Point the usage service's own get_session/engine at a throwaway DB."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from contextlib import contextmanager

    import app.db.models  # noqa: F401
    from app.db.database import Base

    engine = create_engine(f"sqlite:///{tmp_path/'u.db'}",
                            connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    @contextmanager
    def _get_session():
        s = Session()
        try:
            yield s
            s.commit()
        finally:
            s.close()

    monkeypatch.setattr(us_module, "engine", engine)
    monkeypatch.setattr(us_module, "get_session", _get_session)
    yield


class TestMetering:
    def test_enforce_increments_and_caps(self):
        # free plan: chat limit 25 — drive to the cap
        for _ in range(us_module.PLAN_LIMITS["free"]["chat"]):
            usage_service.enforce(1, "free", "chat")
        with pytest.raises(QuotaExceededError):
            usage_service.enforce(1, "free", "chat")

    def test_users_have_independent_counters(self):
        usage_service.enforce(1, "free", "chat")
        u = usage_service.usage(2, "free")
        chat = next(m for m in u["metrics"] if m["metric"] == "chat")
        assert chat["used"] == 0  # user 2 unaffected by user 1

    def test_check_does_not_increment(self):
        usage_service.check(1, "free", "report")
        usage_service.check(1, "free", "report")
        u = usage_service.usage(1, "free")
        report = next(m for m in u["metrics"] if m["metric"] == "report")
        assert report["used"] == 0  # check() never counts

    def test_record_increments(self):
        usage_service.record(1, "report")
        usage_service.record(1, "report")
        u = usage_service.usage(1, "free")
        report = next(m for m in u["metrics"] if m["metric"] == "report")
        assert report["used"] == 2

    def test_pro_plan_higher_limit(self):
        # well past the free cap, pro is fine
        for _ in range(us_module.PLAN_LIMITS["free"]["chat"] + 5):
            usage_service.enforce(9, "pro", "chat")
        assert True  # no QuotaExceededError raised

    def test_usage_report_shape(self):
        u = usage_service.usage(1, "free")
        assert u["plan"] == "free"
        metrics = {m["metric"]: m for m in u["metrics"]}
        assert metrics["chat"]["limit"] == 25 and metrics["report"]["limit"] == 5
