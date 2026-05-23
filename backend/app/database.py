"""
backend/app/database.py
───────────────────────
Dual-engine SQLAlchemy setup:

  ┌─────────────────────────────────────────────────────────────────┐
  │  ASYNC engine (asyncpg)   ← FastAPI async routes, production    │
  │  SYNC  engine (psycopg2)  ← Alembic migrations, pytest, seeds  │
  └─────────────────────────────────────────────────────────────────┘

Usage in async FastAPI endpoint
────────────────────────────────
    from backend.app.database import get_async_db
    from sqlalchemy.ext.asyncio import AsyncSession

    @router.get("/students")
    async def list_students(db: AsyncSession = Depends(get_async_db)):
        result = await db.execute(select(Student))
        ...

Usage in sync endpoint / test
──────────────────────────────
    from backend.app.database import get_db
    from sqlalchemy.orm import Session

    @router.get("/students")
    def list_students(db: Session = Depends(get_db)):
        ...

Environment variables
─────────────────────
    DATABASE_URL      = postgresql+asyncpg://user:pass@host/dbname   (async)
    SYNC_DATABASE_URL = postgresql+psycopg2://user:pass@host/dbname  (sync)

    SQLite is also supported for development / CI:
    DATABASE_URL      = sqlite+aiosqlite:///./jee_dropout.db
    SYNC_DATABASE_URL = sqlite:///./jee_dropout.db
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.config import settings

logger = logging.getLogger(__name__)

# ── URL helpers ───────────────────────────────────────────────────────────────

def _async_url(url: str) -> str:
    """
    Derive an async-compatible URL from a sync URL.

    sqlite     → sqlite+aiosqlite
    postgresql → postgresql+asyncpg
    """
    if url.startswith("sqlite") and "aiosqlite" not in url:
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if url.startswith("postgresql") and "asyncpg" not in url:
        return (
            url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
               .replace("postgresql://", "postgresql+asyncpg://", 1)
        )
    return url


def _sync_url(url: str) -> str:
    """
    Derive a sync-compatible URL from any URL (strips async drivers).

    sqlite+aiosqlite → sqlite
    postgresql+asyncpg → postgresql+psycopg2
    """
    url = url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return url


# ── Derive both URLs from the single settings value ───────────────────────────

_raw_url   = settings.DATABASE_URL
ASYNC_URL  = _async_url(_raw_url)
SYNC_URL   = _sync_url(_raw_url)

_is_sqlite = "sqlite" in SYNC_URL

# ── Async engine (production FastAPI) ─────────────────────────────────────────

_async_connect_args: dict = (
    {"check_same_thread": False} if _is_sqlite else {}
)

async_engine = create_async_engine(
    ASYNC_URL,
    connect_args=_async_connect_args,
    pool_pre_ping=True,
    echo=settings.DEBUG,
    # PostgreSQL pool settings (ignored for SQLite)
    **({} if _is_sqlite else {
        "pool_size":     10,
        "max_overflow":  20,
        "pool_timeout":  30,
        "pool_recycle":  1800,
    }),
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# ── Sync engine (Alembic / pytest / seed scripts) ─────────────────────────────

_sync_connect_args: dict = (
    {"check_same_thread": False} if _is_sqlite else {}
)

engine = create_engine(
    SYNC_URL,
    connect_args=_sync_connect_args,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Enable WAL mode for SQLite (better concurrent read performance)
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── Base class for all ORM models ─────────────────────────────────────────────

class Base(DeclarativeBase):
    """
    Shared declarative base.  All ORM models inherit from this class.
    Registered by importing backend.app.models.database before calling
    Base.metadata.create_all() or running Alembic autogenerate.
    """
    pass


# ── FastAPI async dependency ──────────────────────────────────────────────────

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async SQLAlchemy session and guarantee it is closed after
    the request completes (or raises).

    Usage::

        @router.get("/students")
        async def list_students(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Student))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── FastAPI sync dependency (backward-compat / tests) ────────────────────────

def get_db() -> Generator[Session, None, None]:
    """
    Yield a synchronous SQLAlchemy session.

    Kept for backward compatibility with existing sync routers and all
    pytest tests that override this dependency.

    Usage::

        @router.get("/students")
        def list_students(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Schema helpers ────────────────────────────────────────────────────────────

def create_all_tables() -> None:
    """
    Create all tables defined via Base.metadata using the *sync* engine.
    Intended for development, testing, and the seed script.

    In production use Alembic migrations instead::

        alembic upgrade head
    """
    from backend.app.models import database as _models  # noqa: F401 — registers models
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified.")


async def create_all_tables_async() -> None:
    """Async variant of create_all_tables() — uses the async engine."""
    from backend.app.models import database as _models  # noqa: F401
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified (async).")
