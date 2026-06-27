"""Schemas for developer API keys (/api/keys)."""

from datetime import datetime

from pydantic import Field

from backend.schemas.common import APIModel


class ApiKeyCreate(APIModel):
    name: str = Field(default="API key", max_length=64)


class ApiKeyOut(APIModel):
    """A key as shown in the management UI — never includes the secret."""

    id: int
    name: str
    prefix: str
    last4: str
    created_at: datetime | None = None
    last_used_at: datetime | None = None


class ApiKeyCreated(ApiKeyOut):
    """Returned once, on creation — carries the full raw secret."""

    key: str
