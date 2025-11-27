import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from main import app
from db import get_session
import models

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def engine():
    """Create an in-memory SQLite database for testing"""
    # Use shared in-memory SQLite so all connections see the same DB
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a database session for testing"""
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session):
    """Create a test client with database dependency override"""
    def override_get_session():
        try:
            yield session
        finally:
            session.rollback()
    
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def headers(uid="u1", first="John", last="Doe"):
    """Helper function to create test headers for API requests"""
    return {
        "X-User-Id": uid,
        "X-First-Name": first,
        "X-Last-Name": last,
    }
