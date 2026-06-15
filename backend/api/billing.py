"""Billing endpoints (/api/billing) — Stripe subscription checkout + webhook."""

import logging

from fastapi import APIRouter, Depends, Request

from app.db.models import User
from backend.core.deps import get_current_user
from backend.services.billing_service import billing_service

logger = logging.getLogger("finverse.api")

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout", summary="Start a Pro subscription checkout")
def checkout(user: User = Depends(get_current_user)) -> dict:
    """Create a Stripe Checkout Session and return its URL for the frontend to
    redirect to. Requires billing to be configured (BACKEND_STRIPE_SECRET_KEY)."""
    return {"url": billing_service.create_checkout_session(user)}


@router.post("/webhook", include_in_schema=False)
async def webhook(request: Request) -> dict:
    """Stripe webhook (unauthenticated; verified by signature). Flips the user's
    plan on subscription create/cancel."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        billing_service.handle_event(payload, sig)
    except Exception:
        logger.exception("billing: webhook handling failed")
        # 200 anyway so Stripe doesn't hammer retries on a parse bug; the
        # exception is logged for us to investigate.
    return {"received": True}
