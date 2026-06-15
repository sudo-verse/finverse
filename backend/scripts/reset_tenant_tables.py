"""One-off 'start clean' migration for SaaS Phase 1 multi-tenancy.

Per-user tables gained a `user_id` column. Pre-SaaS data was single-tenant and
global (disposable), so rather than backfill we DROP and recreate these tables.
Run once:  python -m backend.scripts.reset_tenant_tables

Going forward, schema changes should go through Alembic (next infra step).
"""

from app.db import models  # noqa: F401 — registers tables on Base.metadata
from app.db.database import Base, engine
from app.db.models import (
    AlertEvent,
    AlertRule,
    PortfolioHolding,
    ResearchChat,
    WatchlistItem,
)

# Drop order is FK-safe: alert_events references alert_rules.
PER_USER_TABLES = [AlertEvent, ResearchChat, WatchlistItem, PortfolioHolding, AlertRule]


def run() -> None:
    for model in PER_USER_TABLES:
        model.__table__.drop(engine, checkfirst=True)
    Base.metadata.create_all(engine)  # recreate with user_id (+ ensure users)
    print("tenant tables reset (start clean):",
          ", ".join(m.__tablename__ for m in PER_USER_TABLES))


if __name__ == "__main__":
    run()
