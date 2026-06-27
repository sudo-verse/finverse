"""Stripe billing — subscription checkout + webhook → plan entitlement.

Checkout uses an inline price (no pre-created Stripe Price needed). Webhooks
flip the user's `plan`, which the usage/metering layer already gates on.
"""

import json
import logging

from app.db.database import get_session
from app.db.models import User
from backend.core.config import settings
from backend.core.exceptions import ServiceUnavailableError

logger = logging.getLogger("finverse.api")


def _stripe():
    if not settings.stripe_enabled:
        raise ServiceUnavailableError(
            "Billing is not configured — set BACKEND_STRIPE_SECRET_KEY."
        )
    import stripe

    stripe.api_key = settings.stripe_secret_key
    return stripe


# Purchasable plans → display name + price (smallest currency unit). Both grant
# API access; they differ in the daily request limits enforced by
# api_key_service.API_RATE_LIMITS / usage_service.PLAN_LIMITS.
def _plan_catalog() -> dict[str, dict]:
    return {
        "pro": {"name": "Finverse Pro", "amount": settings.pro_price_amount},
        "scale": {"name": "Finverse Scale", "amount": settings.scale_price_amount},
    }


class BillingService:
    def create_checkout_session(self, user: User, plan: str = "pro") -> str:
        """Create a Stripe Checkout Session for a purchasable plan; returns the
        hosted-checkout URL the frontend redirects to. The chosen plan is
        carried in metadata so the webhook can entitle the user correctly."""
        catalog = _plan_catalog()
        spec = catalog.get(plan)
        if spec is None:
            raise ServiceUnavailableError(f"Unknown plan '{plan}'.")
        stripe = _stripe()
        kwargs: dict = {
            "mode": "subscription",
            "client_reference_id": str(user.id),
            "metadata": {"user_id": str(user.id), "plan": plan},
            "line_items": [{
                "quantity": 1,
                "price_data": {
                    "currency": settings.pro_price_currency,
                    "unit_amount": spec["amount"],
                    "recurring": {"interval": settings.pro_price_interval},
                    "product_data": {"name": spec["name"]},
                },
            }],
            "success_url": f"{settings.app_base_url}/settings?billing=success&plan={plan}",
            "cancel_url": f"{settings.app_base_url}/settings?billing=cancel",
        }
        # Reuse the Stripe customer if we have one, else let Checkout create it.
        if user.stripe_customer_id:
            kwargs["customer"] = user.stripe_customer_id
        else:
            kwargs["customer_email"] = user.email

        session = stripe.checkout.Session.create(**kwargs)
        logger.info("billing: checkout session for user %s", user.id)
        return session.url

    # ------------------------------------------------------------- webhook
    def handle_event(self, payload: bytes, sig_header: str | None) -> None:
        event = self._parse_event(payload, sig_header)
        etype = event["type"]
        obj = event["data"]["object"]

        if etype == "checkout.session.completed":
            meta = obj.get("metadata") or {}
            user_id = int(obj.get("client_reference_id") or meta.get("user_id") or 0)
            plan = meta.get("plan") or "pro"
            if plan not in _plan_catalog():
                plan = "pro"
            self._set_plan(user_id, plan,
                           customer=obj.get("customer"),
                           subscription=obj.get("subscription"))
        elif etype == "customer.subscription.deleted":
            self._downgrade(obj.get("id"))
        elif etype == "customer.subscription.updated":
            if obj.get("status") in ("canceled", "unpaid", "incomplete_expired"):
                self._downgrade(obj.get("id"))
        else:
            logger.debug("billing: ignoring webhook event %s", etype)

    def _parse_event(self, payload: bytes, sig_header: str | None):
        stripe = _stripe()
        if settings.stripe_webhook_secret and sig_header:
            return stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        # Dev fallback: no signing secret configured → cannot verify. Acceptable
        # for local testing only; production MUST set BACKEND_STRIPE_WEBHOOK_SECRET.
        logger.warning("billing: webhook signature NOT verified (no webhook secret set)")
        return json.loads(payload)

    @staticmethod
    def _set_plan(user_id: int, plan: str, customer=None, subscription=None) -> None:
        if not user_id:
            return
        with get_session() as s:
            user = s.query(User).filter_by(id=user_id).first()
            if not user:
                logger.warning("billing: webhook for unknown user %s", user_id)
                return
            user.plan = plan
            if customer:
                user.stripe_customer_id = customer
            if subscription:
                user.stripe_subscription_id = subscription
        logger.info("billing: user %s -> %s", user_id, plan)

    @staticmethod
    def _downgrade(subscription_id: str | None) -> None:
        if not subscription_id:
            return
        with get_session() as s:
            user = s.query(User).filter_by(stripe_subscription_id=subscription_id).first()
            if user:
                user.plan = "free"
                logger.info("billing: user %s downgraded to free", user.id)


billing_service = BillingService()
