"""Shared FastAPI dependencies for authentication / tenancy scoping."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.models import User
from backend.core.database import get_db
from backend.core.exceptions import UnauthorizedError
from backend.core.security import decode_access_token
from backend.services.auth_service import auth_service

# auto_error=False so a missing token raises our UnauthorizedError (401 with
# WWW-Authenticate) instead of FastAPI's default 403.
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a Bearer JWT, or raise 401.

    Every per-user (tenant-scoped) endpoint depends on this and scopes its
    queries to the returned user's id."""
    if creds is None or not creds.credentials:
        raise UnauthorizedError("Not authenticated.")
    payload = decode_access_token(creds.credentials)
    if not payload or not payload.get("sub"):
        raise UnauthorizedError("Invalid or expired token.")
    user = auth_service.get_by_id(db, int(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("User no longer exists.")
    return user


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None instead of raising when no/invalid
    token — for endpoints that are public but enrich the response when signed in
    (e.g. the dashboard's portfolio card)."""
    if creds is None or not creds.credentials:
        return None
    payload = decode_access_token(creds.credentials)
    if not payload or not payload.get("sub"):
        return None
    user = auth_service.get_by_id(db, int(payload["sub"]))
    return user if (user and user.is_active) else None
