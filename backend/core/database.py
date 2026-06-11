"""FastAPI database dependency.

Reuses the existing SQLAlchemy engine/session factory from `app.db.database`
so the API shares connection pooling and models with the engine and ETL.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped session (read-mostly; commits on success)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
