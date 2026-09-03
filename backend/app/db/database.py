"""
Database engine and session setup (SQLAlchemy 2.x).

Reads DATABASE_URL from the environment.
Defaults to a local SQLite file for easy local testing.

Production example:
    DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE

Local / CI testing:
    DATABASE_URL=sqlite:///./local_test.db
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# ── Configuration ──────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local_test.db")

# SQLite requires check_same_thread=False when used with FastAPI
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)

# Each request gets its own session, auto-closed in the dependency
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Declarative base for all ORM models ────────────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ──────────────────────────────────────────
def get_db():
    """
    Yield a database session for a single request, then close it.
    Used with FastAPI's Depends() system.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Startup helper ─────────────────────────────────────────────
def init_db() -> None:
    """
    Create all tables defined in ORM models.
    Called once at application startup via the lifespan context manager.
    Safe to call multiple times (CREATE TABLE IF NOT EXISTS behaviour).
    """
    # Import models here so SQLAlchemy registers them before create_all
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
