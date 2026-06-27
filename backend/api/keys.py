"""Developer API key management (/api/keys).

Issue, list and revoke keys for the public API. These endpoints are tenant
operations — they authenticate with a session JWT (or another API key) and act
on the caller's own keys only. The raw secret is returned exactly once, by
POST /keys; after that only its prefix/last4 are ever exposed.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import User
from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyOut
from backend.services.api_key_service import api_key_service

router = APIRouter(prefix="/keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyOut], summary="List your API keys")
def list_keys(user: User = Depends(get_current_user),
              db: Session = Depends(get_db)) -> list[ApiKeyOut]:
    return [ApiKeyOut.model_validate(k) for k in api_key_service.list(db, user)]


@router.post("", response_model=ApiKeyCreated, status_code=201,
             summary="Create an API key")
def create_key(payload: ApiKeyCreate, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)) -> ApiKeyCreated:
    """Mint a new key. The full secret is in the `key` field of the response and
    is shown only this once — store it securely."""
    row, raw = api_key_service.create(db, user, payload.name)
    return ApiKeyCreated.model_validate({**row.__dict__, "key": raw})


@router.delete("/{key_id}", status_code=204, summary="Revoke an API key")
def revoke_key(key_id: int, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)) -> None:
    api_key_service.revoke(db, user, key_id)
