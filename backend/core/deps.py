"""Shared FastAPI dependencies for authentication / tenancy scoping."""

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.models import User
from backend.core.database import get_db
from backend.core.exceptions import UnauthorizedError
from backend.core.security import decode_access_token
from backend.services.api_key_service import _PREFIX, api_key_service, required_scope
from backend.services.auth_service import auth_service

# auto_error=False so a missing token raises our UnauthorizedError (401 with
# WWW-Authenticate) instead of FastAPI's default 403.
_bearer = HTTPBearer(auto_error=False)


def _user_from_api_key(db: Session, raw: str, request: Request) -> User | None:
    """Resolve a developer API key and enforce its limits. Returns the owning
    user, or None if the key is unknown/revoked. Enforces, in order:
    scope (403 if the key lacks the capability this request needs), burst
    throttle (429 + Retry-After), and the daily quota (429)."""
    key = api_key_service.authenticate(db, raw)
    if key is None:
        return None
    user = auth_service.get_by_id(db, key.user_id)
    if user is None or not user.is_active:
        return None
    need = required_scope(request.method, request.url.path)
    if need not in api_key_service.scopes_of(key):
        raise HTTPException(
            status_code=403,
            detail=f"API key lacks the '{need}' scope required for this request.",
        )
    api_key_service.throttle(key, user.plan)    # 429 (Retry-After) on burst
    api_key_service.meter(db, key, user.plan)   # 429 when over daily quota
    return user


def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a Bearer credential, or raise 401.

    Accepts either a session JWT (the web app) or a developer API key
    (``fv_live_…`` — the public API). Every per-user (tenant-scoped) endpoint
    depends on this and scopes its queries to the returned user's id."""
    if creds is None or not creds.credentials:
        raise UnauthorizedError("Not authenticated.")
    token = creds.credentials
    if token.startswith(_PREFIX):
        user = _user_from_api_key(db, token, request)
        if user is None:
            raise UnauthorizedError("Invalid or revoked API key.")
        return user
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise UnauthorizedError("Invalid or expired token.")
    user = auth_service.get_by_id(db, int(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("User no longer exists.")
    return user


def get_current_user_optional(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None instead of raising when no/invalid
    token — for endpoints that are public but enrich the response when signed in
    (e.g. the dashboard's portfolio card)."""
    if creds is None or not creds.credentials:
        return None
    token = creds.credentials
    if token.startswith(_PREFIX):
        return _user_from_api_key(db, token, request)
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        return None
    user = auth_service.get_by_id(db, int(payload["sub"]))
    return user if (user and user.is_active) else None
