"""Schemas for developer API keys (/api/keys)."""

from datetime import datetime

from pydantic import Field

from backend.schemas.common import APIModel


class ApiKeyCreate(APIModel):
    name: str = Field(default="API key", max_length=64)
    # Capabilities to grant: any of read / ai / write. Empty → default grant set.
    scopes: list[str] = Field(default_factory=lambda: ["read", "ai", "write"])


class ApiKeyOut(APIModel):
    """A key as shown in the management UI — never includes the secret."""

    id: int
    name: str
    prefix: str
    last4: str
    scopes: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    last_used_at: datetime | None = None


class ApiKeyCreated(ApiKeyOut):
    """Returned once, on creation — carries the full raw secret."""

    key: str
