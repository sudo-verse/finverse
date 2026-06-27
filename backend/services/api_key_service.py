"""Developer API keys — issue, list, revoke, authenticate and meter.

Keys look like ``fv_live_<43 url-safe chars>``. We persist only a SHA-256 hash
(keys are high-entropy, so a fast hash is safe and lets us look them up in one
indexed query); the raw secret is returned exactly once, at creation.

Every authenticated API call is counted per key per day and rejected with 429
once the owner's plan limit is reached — this is the metering the public API
pricing is built on. Tables self-create (checkfirst) to match the codebase's
no-Alembic deploy path, like usage_service / saved_screen_service.
"""

import hashlib
import logging
import secrets
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.database import engine
from app.db.models import ApiKey, ApiKeyUsage, User
from backend.core.exceptions import NotFoundError, QuotaExceededError

logger = logging.getLogger("finverse.api")

_PREFIX = "fv_live_"
_MAX_KEYS = 10                 # active keys per user
_LAST_USED_THROTTLE = 300      # only touch last_used_at every N seconds

# Daily request cap per plan (None = unlimited). Mirrors the Developers pricing.
API_RATE_LIMITS: dict[str, int | None] = {
    "free": 1_000,
    "pro": 50_000,
    "scale": 250_000,
}
_FALLBACK_LIMIT = API_RATE_LIMITS["free"]


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class ApiKeyService:
    _ready = False

    def _ensure_tables(self) -> None:
        if not self._ready:
            ApiKey.__table__.create(engine, checkfirst=True)
            ApiKeyUsage.__table__.create(engine, checkfirst=True)
            self._ready = True

    # --------------------------------------------------------------- issuance
    def create(self, db: Session, user: User, name: str | None = None) -> tuple[ApiKey, str]:
        """Mint a new key for ``user``. Returns (row, raw_secret); the raw
        secret is only available here and never stored in clear."""
        self._ensure_tables()
        active = (db.query(ApiKey)
                  .filter(ApiKey.user_id == user.id, ApiKey.revoked_at.is_(None))
                  .count())
        if active >= _MAX_KEYS:
            raise QuotaExceededError(
                f"Key limit reached ({_MAX_KEYS}). Revoke an existing key first."
            )
        token = secrets.token_urlsafe(32)
        raw = f"{_PREFIX}{token}"
        row = ApiKey(
            user_id=user.id,
            name=(name or "API key").strip()[:64] or "API key",
            prefix=f"{_PREFIX}{token[:6]}",
            last4=token[-4:],
            hashed_key=_hash(raw),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        logger.info("api_key: user %s minted key %s", user.id, row.prefix)
        return row, raw

    def list(self, db: Session, user: User) -> list[ApiKey]:
        self._ensure_tables()
        return (db.query(ApiKey)
                .filter(ApiKey.user_id == user.id, ApiKey.revoked_at.is_(None))
                .order_by(ApiKey.created_at.desc())
                .all())

    def revoke(self, db: Session, user: User, key_id: int) -> None:
        self._ensure_tables()
        row = (db.query(ApiKey)
               .filter(ApiKey.id == key_id, ApiKey.user_id == user.id,
                       ApiKey.revoked_at.is_(None))
               .first())
        if row is None:
            raise NotFoundError("API key not found.")
        row.revoked_at = datetime.utcnow()
        db.commit()
        logger.info("api_key: user %s revoked key %s", user.id, row.prefix)

    # --------------------------------------------------------- authentication
    def authenticate(self, db: Session, raw: str) -> ApiKey | None:
        """Resolve a raw key to its (non-revoked) row, or None."""
        self._ensure_tables()
        if not raw.startswith(_PREFIX):
            return None
        row = (db.query(ApiKey)
               .filter(ApiKey.hashed_key == _hash(raw), ApiKey.revoked_at.is_(None))
               .first())
        if row is None:
            return None
        # Throttled last-used touch — avoid a write on every single request.
        now = datetime.utcnow()
        if row.last_used_at is None or (now - row.last_used_at) > timedelta(seconds=_LAST_USED_THROTTLE):
            row.last_used_at = now
            db.commit()
        return row

    def meter(self, db: Session, key: ApiKey, plan: str) -> None:
        """Count one request against the key's daily quota; raise 429 if over."""
        limit = API_RATE_LIMITS.get(plan, _FALLBACK_LIMIT)
        today = date.today()
        row = (db.query(ApiKeyUsage)
               .filter(ApiKeyUsage.api_key_id == key.id, ApiKeyUsage.day == today)
               .first())
        used = row.count if row else 0
        if limit is not None and used >= limit:
            raise QuotaExceededError(
                f"API rate limit reached for the {plan} plan ({limit}/day). "
                f"Upgrade for higher limits."
            )
        if row:
            row.count += 1
        else:
            db.add(ApiKeyUsage(api_key_id=key.id, day=today, count=1))
        db.commit()


api_key_service = ApiKeyService()
