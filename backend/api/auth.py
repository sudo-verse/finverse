"""Authentication endpoints (/api/auth/*).

Email + password with bcrypt hashing; returns a JWT bearer token used by all
tenant-scoped endpoints (sent as `Authorization: Bearer <token>`).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import User
from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.schemas.auth import LoginRequest, RegisterRequest, TokenOut, UserOut
from backend.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201,
             summary="Create an account")
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenOut:
    """Register a new user and return an access token."""
    return auth_service.register(db, payload)


@router.post("/login", response_model=TokenOut, summary="Log in")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    """Authenticate and return an access token."""
    return auth_service.login(db, payload.email, payload.password)


@router.get("/me", response_model=UserOut, summary="Current user")
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
