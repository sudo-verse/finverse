"""Cashfree billing — India-first plan upgrades (INR via UPI / cards / netbanking).

Mirrors the Stripe flow: create a Cashfree PG order → the frontend opens
Cashfree's hosted checkout with the returned ``payment_session_id`` → on
payment, Cashfree calls our webhook, which (after HMAC verification) flips the
user's ``plan`` via the shared billing helper.

Recurring auto-renewal (Cashfree Subscriptions / UPI-autopay mandates) is a
heavier integration; this implements period activation on each successful
payment, which is enough to sell and entitle a plan.
"""

import base64
import hashlib
import hmac
import logging
import time
import uuid

import requests

from app.db.models import User
from backend.core.config import settings
from backend.core.exceptions import ServiceUnavailableError
from backend.services.billing_service import billing_service

logger = logging.getLogger("finverse.api")

_API_VERSION = "2023-08-01"
_TIMEOUT = 20


def _base_url() -> str:
    return (
        "https://api.cashfree.com/pg"
        if settings.cashfree_env == "production"
        else "https://sandbox.cashfree.com/pg"
    )


def _headers() -> dict:
    return {
        "x-client-id": settings.cashfree_app_id,
        "x-client-secret": settings.cashfree_secret_key,
        "x-api-version": _API_VERSION,
        "Content-Type": "application/json",
    }


def plan_catalog() -> dict[str, dict]:
    """Purchasable plans → display name + INR amount. Same tiers as Stripe."""
    return {
        "pro": {"name": "Finverse Pro", "amount": settings.pro_price_inr},
        "scale": {"name": "Finverse Scale", "amount": settings.scale_price_inr},
    }


class CashfreeService:
    def create_order(self, user: User, plan: str = "pro") -> dict:
        """Create a Cashfree order for ``plan``; return the data the frontend
        SDK needs to open hosted checkout (payment_session_id + order_id)."""
        spec = plan_catalog().get(plan)
        if spec is None:
            raise ServiceUnavailableError(f"Unknown plan '{plan}'.")
        if not settings.cashfree_enabled:
            raise ServiceUnavailableError(
                "Cashfree is not configured — set BACKEND_CASHFREE_APP_ID and "
                "BACKEND_CASHFREE_SECRET_KEY."
            )
        order_id = f"fv_{user.id}_{plan}_{uuid.uuid4().hex[:12]}"
        return_url = f"{settings.app_base_url}/settings?billing=success&gw=cashfree&order_id={{order_id}}"
        body = {
            "order_id": order_id,
            "order_amount": float(spec["amount"]),
            "order_currency": "INR",
            "customer_details": {
                "customer_id": f"user_{user.id}",
                "customer_email": user.email,
                "customer_phone": settings.cashfree_default_phone,
            },
            "order_meta": {"return_url": return_url, "notify_url": self._notify_url()},
            "order_note": spec["name"],
            "order_tags": {"plan": plan, "user_id": str(user.id)},
        }
        resp = requests.post(
            f"{_base_url()}/orders", json=body, headers=_headers(), timeout=_TIMEOUT
        )
        if resp.status_code >= 400:
            logger.error("cashfree: create order failed %s %s", resp.status_code, resp.text[:300])
            raise ServiceUnavailableError("Could not start Cashfree checkout. Try again.")
        data = resp.json()
        logger.info("cashfree: order %s for user %s plan %s", data.get("order_id"), user.id, plan)
        return {
            "payment_session_id": data.get("payment_session_id"),
            "order_id": data.get("order_id"),
            "mode": "production" if settings.cashfree_env == "production" else "sandbox",
        }

    @staticmethod
    def _notify_url() -> str:
        base = (settings.api_base_url or settings.app_base_url).rstrip("/")
        return f"{base}/api/billing/cashfree/webhook"

    # ------------------------------------------------------------- webhook
    def verify(self, raw: bytes, signature: str | None, timestamp: str | None) -> bool:
        """Cashfree signs ``timestamp + rawBody`` with the secret key (HMAC-SHA256,
        base64). Returns True when the signature matches."""
        if not signature or not timestamp:
            return False
        msg = (timestamp + raw.decode("utf-8")).encode("utf-8")
        digest = hmac.new(settings.cashfree_secret_key.encode(), msg, hashlib.sha256).digest()
        expected = base64.b64encode(digest).decode()
        return hmac.compare_digest(expected, signature)

    def handle_webhook(self, raw: bytes, signature: str | None, timestamp: str | None) -> None:
        if settings.cashfree_secret_key and not self.verify(raw, signature, timestamp):
            logger.warning("cashfree: webhook signature mismatch — ignoring")
            return
        import json

        event = json.loads(raw or b"{}")
        etype = (event.get("type") or "").upper()
        data = event.get("data") or {}
        order = data.get("order") or {}
        payment = data.get("payment") or {}

        paid = (
            "SUCCESS" in etype
            or (payment.get("payment_status") or "").upper() == "SUCCESS"
            or (order.get("order_status") or "").upper() == "PAID"
        )
        if not paid:
            logger.debug("cashfree: ignoring webhook %s", etype)
            return

        tags = order.get("order_tags") or {}
        plan = tags.get("plan") or "pro"
        if plan not in plan_catalog():
            plan = "pro"
        try:
            user_id = int(tags.get("user_id") or 0)
        except (TypeError, ValueError):
            user_id = 0
        if not user_id:
            logger.warning("cashfree: paid webhook without user_id (order %s)", order.get("order_id"))
            return
        billing_service._set_plan(user_id, plan)
        logger.info("cashfree: user %s -> %s (order %s)", user_id, plan, order.get("order_id"))


cashfree_service = CashfreeService()
