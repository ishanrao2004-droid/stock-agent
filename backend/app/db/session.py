"""
db/session.py
─────────────
SQLAlchemy async-capable session factory and dependency injection helper
for FastAPI route handlers.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from backend.app.core.config import settings


# ── Engine ───────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # Detect stale connections before use
    pool_size=10,
    max_overflow=20,
    echo=False  # Disabled to prevent log flooding,
)

# ── Session factory ──────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Prevents lazy-load errors after commit
)


# ── Base class for all ORM models ────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ───────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Yields a database session and ensures it is closed after the request,
    even if an exception is raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Context manager for scripts / Celery tasks ───────────────────────────────
@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context-manager version for use outside FastAPI (scripts, workers)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
