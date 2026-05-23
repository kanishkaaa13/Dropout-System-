"""
migrations/env.py
─────────────────
Alembic environment supporting BOTH async (production) and sync (CLI) modes.

Run migrations
--------------
    # Apply all pending migrations
    alembic upgrade head

    # Generate a new auto-migration from model changes
    alembic revision --autogenerate -m "add_xyz_column"

    # Downgrade one step
    alembic downgrade -1

Environment variables required
-------------------------------
    DATABASE_URL   — e.g. postgresql+asyncpg://user:pass@host/dbname
                         or sqlite:///./jee_dropout.db (dev/CI)

Design
------
• Alembic's CLI runs synchronously, so we use the sync engine for migration
  execution (run_migrations_online runs asyncio.run() when the URL is async).
• run_migrations_offline() uses the literal URL from settings (no DB needed).
• Autogenerate compares Base.metadata against the live DB schema.
"""

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import create_async_engine

# ── Make project root importable ──────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Load app config + models ──────────────────────────────────────────────────
from backend.app.config import settings          # noqa: E402
from backend.app.database import SYNC_URL, ASYNC_URL, Base  # noqa: E402
import backend.app.models.database as _models    # noqa: E402, F401 — registers all models

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Inject the sync DB URL so Alembic CLI can connect
config.set_main_option("sqlalchemy.url", SYNC_URL)

# Wire up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata


# ── Naming convention (required for reliable autogenerate on PostgreSQL) ───────
# Applied globally so Alembic generates named constraints that can be dropped.
from sqlalchemy import MetaData  # noqa: E402

naming_convention = {
    "ix":  "ix_%(column_0_label)s",
    "uq":  "uq_%(table_name)s_%(column_0_name)s",
    "ck":  "ck_%(table_name)s_%(constraint_name)s",
    "fk":  "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk":  "pk_%(table_name)s",
}
target_metadata.naming_convention = naming_convention


# ── Offline mode (generates SQL without DB connection) ────────────────────────

def run_migrations_offline() -> None:
    """
    Run migrations without a live DB connection.
    Useful for generating SQL scripts to review before applying.

        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,   # required for SQLite ALTER TABLE support
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online sync mode (used by CLI with sync URL) ──────────────────────────────

def run_migrations_online_sync() -> None:
    """Run migrations against the sync DB engine (default Alembic mode)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# ── Online async mode (optional — for use in async test suites) ───────────────

async def run_migrations_online_async() -> None:
    """Run migrations via the async engine (useful in async test fixtures)."""
    connectable = create_async_engine(ASYNC_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(
                connection=conn,
                target_metadata=target_metadata,
                render_as_batch=True,
                compare_type=True,
                compare_server_default=True,
            )
        )
        async with connection.begin():
            await connection.run_sync(lambda conn: context.run_migrations())

    await connectable.dispose()


# ── Entry point ───────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    # Use sync mode for CLI; async is available for programmatic use
    run_migrations_online_sync()
