"""
Test configuration and shared fixtures.

Sets GEMINI_MOCK=true and DATABASE_URL to a local SQLite file
BEFORE the app is imported, so no real API key or PostgreSQL is needed.

Run from the backend/ directory:
    pytest tests/ -v
"""

import os

# ── Set test env vars BEFORE importing the app ──────────────────
os.environ.setdefault("GEMINI_MOCK", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_local.db")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app

# ── Dedicated SQLite DB for tests ────────────────────────────────
TEST_DB_URL = "sqlite:///./test_local.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Replace the production DB session with a test session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create tables once before all tests; drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def client(setup_test_database):
    """FastAPI TestClient with the DB dependency overridden."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
