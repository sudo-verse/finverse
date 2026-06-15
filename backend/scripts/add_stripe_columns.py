"""Add Stripe columns to the users table (idempotent).

stripe_customer_id / stripe_subscription_id are nullable, so SQLite can add
them in place without a table rebuild. Run once:
    python -m backend.scripts.add_stripe_columns
(Postgres + Alembic will own migrations going forward.)
"""

from sqlalchemy import inspect, text

from app.db.database import engine

COLUMNS = {
    "stripe_customer_id": "VARCHAR(64)",
    "stripe_subscription_id": "VARCHAR(64)",
}


def run() -> None:
    existing = {c["name"] for c in inspect(engine).get_columns("users")}
    with engine.begin() as conn:
        for name, ddl in COLUMNS.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
                print(f"added users.{name}")
            else:
                print(f"users.{name} already present")


if __name__ == "__main__":
    run()
