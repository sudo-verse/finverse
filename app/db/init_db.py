from app.db.database import engine, Base
from app.db import models  # noqa: F401  (registers models on Base.metadata)
from app.utils.logger import logger


def init_db():
    """Ensure the schema exists.

    SQLite (local dev): create_all for zero-setup convenience. Postgres (prod):
    schema is owned by Alembic — run `alembic upgrade head` on deploy; we skip
    create_all so it can't race the migrations.
    """
    if engine.url.get_backend_name().startswith("postgres"):
        logger.info("Database: Postgres detected — schema managed by Alembic "
                    "(run `alembic upgrade head`). Skipping create_all.")
        return
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized: {engine.url}")


if __name__ == "__main__":
    init_db()
