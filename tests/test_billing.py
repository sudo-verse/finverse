"""Billing: webhook → plan entitlement, and checkout session creation
(Stripe calls are stubbed; DB is isolated)."""

import json
from contextlib import contextmanager

import pytest

from backend.services import billing_service as bs_module
from backend.services.billing_service import billing_service


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Isolate the billing service's get_session and seed a user."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import app.db.models  # noqa: F401
    from app.db.database import Base
    from app.db.models import User

    engine = create_engine(f"sqlite:///{tmp_path/'b.db'}",
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

    monkeypatch.setattr(bs_module, "get_session", _get_session)

    s = Session()
    s.add(User(id=1, email="a@example.com", hashed_password="x", plan="free"))
    s.commit()
    s.close()
    return Session


def _plan(Session, user_id=1):
    from app.db.models import User
    s = Session()
    try:
        return s.query(User).filter_by(id=user_id).first().plan
    finally:
        s.close()


class TestWebhook:
    def test_checkout_completed_upgrades_to_pro(self, db, monkeypatch):
        # no webhook secret → dev fallback parses raw JSON (no signature)
        monkeypatch.setattr(bs_module.settings, "stripe_webhook_secret", "", raising=False)
        monkeypatch.setattr(bs_module.settings, "stripe_secret_key", "sk_test_x", raising=False)
        event = {
            "type": "checkout.session.completed",
            "data": {"object": {
                "client_reference_id": "1",
                "customer": "cus_123",
                "subscription": "sub_123",
            }},
        }
        billing_service.handle_event(json.dumps(event).encode(), None)
        assert _plan(db) == "pro"

    def test_subscription_deleted_downgrades(self, db, monkeypatch):
        monkeypatch.setattr(bs_module.settings, "stripe_webhook_secret", "", raising=False)
        monkeypatch.setattr(bs_module.settings, "stripe_secret_key", "sk_test_x", raising=False)
        # upgrade first, with a known subscription id
        billing_service._set_plan(1, "pro", customer="cus_1", subscription="sub_1")
        assert _plan(db) == "pro"
        billing_service.handle_event(
            json.dumps({"type": "customer.subscription.deleted",
                        "data": {"object": {"id": "sub_1"}}}).encode(), None)
        assert _plan(db) == "free"

    def test_unknown_event_ignored(self, db, monkeypatch):
        monkeypatch.setattr(bs_module.settings, "stripe_webhook_secret", "", raising=False)
        monkeypatch.setattr(bs_module.settings, "stripe_secret_key", "sk_test_x", raising=False)
        billing_service.handle_event(
            json.dumps({"type": "invoice.paid", "data": {"object": {}}}).encode(), None)
        assert _plan(db) == "free"  # unchanged


class TestCheckout:
    def test_create_checkout_returns_url(self, db, monkeypatch):
        monkeypatch.setattr(bs_module.settings, "stripe_secret_key", "sk_test_x", raising=False)

        class _FakeSession:
            url = "https://checkout.stripe.test/session/abc"

        class _FakeCheckout:
            Session = type("S", (), {"create": staticmethod(lambda **kw: _FakeSession())})

        fake_stripe = type("Stripe", (), {"checkout": _FakeCheckout, "api_key": None})
        monkeypatch.setattr(bs_module, "_stripe", lambda: fake_stripe)

        from app.db.models import User
        user = User(id=1, email="a@example.com", hashed_password="x", plan="free")
        url = billing_service.create_checkout_session(user)
        assert url.startswith("https://checkout.stripe.test/")
