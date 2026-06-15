"""Authentication service — registration, login, and user lookup."""

import logging

from sqlalchemy.orm import Session

from app.db.models import User
from backend.core.exceptions import ConflictError, UnauthorizedError
from backend.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.schemas.auth import RegisterRequest, TokenOut, UserOut

logger = logging.getLogger("finverse.api")


class AuthService:
    def register(self, db: Session, payload: RegisterRequest) -> TokenOut:
        if db.query(User.id).filter(User.email == payload.email).first():
            raise ConflictError("An account with this email already exists.")
        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            plan="free",
        )
        db.add(user)
        db.flush()  # assign user.id before we build the token
        logger.info("auth: registered user %s (id=%s)", user.email, user.id)
        return self._token(user)

    def login(self, db: Session, email: str, password: str) -> TokenOut:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password.")
        if not user.is_active:
            raise UnauthorizedError("This account is disabled.")
        return self._token(user)

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def _token(user: User) -> TokenOut:
        return TokenOut(
            access_token=create_access_token(user.id, user.email),
            user=UserOut.model_validate(user),
        )


auth_service = AuthService()
