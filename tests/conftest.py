"""
tests/conftest.py
─────────────────
Shared pytest fixtures for all router tests.

Uses an in-memory SQLite database so tests are:
  - Isolated from production data
  - Fast (no I/O)
  - Idempotent (fresh DB per test session)

Run tests:
    pytest tests/ -v
"""

from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Make project root importable ─────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Override DATABASE_URL before any app import ──────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_jee.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("MODEL_DIR", "models")
# NOTE: use @jeetest.com not @jee.test — .test is RFC-2606 reserved and
# rejected by email-validator's deliverability check.

from backend.app.database import Base, get_db          # noqa: E402
from backend.app.main import create_app                 # noqa: E402
from backend.app.middleware.auth import hash_password   # noqa: E402
from backend.app.models.database import User            # noqa: E402

# ── In-memory test engine ────────────────────────────────────────────────────
TEST_DB_URL = "sqlite:///./test_jee.db"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)

TestingSession = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


# ── Create tables once per session ───────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    import backend.app.models.database as _models  # noqa: F401 — registers models
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    # Dispose engine to release Windows file lock before deleting
    test_engine.dispose()
    try:
        if os.path.exists("test_jee.db"):
            os.remove("test_jee.db")
    except PermissionError:
        pass   # Windows may still hold the lock; file will be overwritten next run


# ── Seed: one admin + one faculty user ───────────────────────────────────────

@pytest.fixture(scope="session")
def seeded_users(create_tables):
    db = TestingSession()
    admin = User(
        email="admin@jeetest.com",
        hashed_password=hash_password("AdminPass123"),
        full_name="Test Admin",
        role="admin",
        is_active=True,
    )
    faculty = User(
        email="faculty@jeetest.com",
        hashed_password=hash_password("FacultyPass123"),
        full_name="Test Faculty",
        role="faculty",
        is_active=True,
    )
    db.add_all([admin, faculty])
    db.commit()
    db.refresh(admin)
    db.refresh(faculty)
    db.close()
    return {"admin": admin, "faculty": faculty}


# ── TestClient fixture ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client(seeded_users):
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Auth token helpers ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def admin_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@jeetest.com", "password": "AdminPass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def faculty_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "faculty@jeetest.com", "password": "FacultyPass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def faculty_headers(faculty_token):
    return {"Authorization": f"Bearer {faculty_token}"}
