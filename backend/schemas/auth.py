"""Schemas for authentication (/api/auth/*)."""

import re
from datetime import datetime

from pydantic import Field, field_validator

from backend.schemas.common import APIModel

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class _WithEmail(APIModel):
    email: str = Field(max_length=255)

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("invalid email address")
        return v


class RegisterRequest(_WithEmail):
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=128)


class LoginRequest(_WithEmail):
    password: str = Field(min_length=1, max_length=128)


class UserOut(APIModel):
    id: int
    email: str
    full_name: str | None = None
    plan: str
    created_at: datetime | None = None


class TokenOut(APIModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
