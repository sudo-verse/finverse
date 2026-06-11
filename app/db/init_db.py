from app.db.database import engine, Base
from app.db import models  # noqa: F401  (registers models on Base.metadata)
from app.utils.logger import logger


def init_db():
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized: {engine.url}")


if __name__ == "__main__":
    init_db()
