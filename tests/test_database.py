# ABOUTME: Tests for database setup — SQLite pragmas and migration runner.
# ABOUTME: Verifies WAL mode, foreign keys, busy_timeout, and schema_migrations tracking.
import pytest
from sqlalchemy import text

from adhdaf.database import create_app_engine, run_migrations


@pytest.mark.asyncio
async def test_sqlite_wal_mode(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_app_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA journal_mode"))
        mode = result.scalar()
    await engine.dispose()
    assert mode == "wal"


@pytest.mark.asyncio
async def test_sqlite_foreign_keys_enabled(db_engine):
    async with db_engine.connect() as conn:
        result = await conn.execute(text("PRAGMA foreign_keys"))
        enabled = result.scalar()
    assert enabled == 1


@pytest.mark.asyncio
async def test_sqlite_busy_timeout(db_engine):
    async with db_engine.connect() as conn:
        result = await conn.execute(text("PRAGMA busy_timeout"))
        timeout = result.scalar()
    assert timeout == 5000


@pytest.mark.asyncio
async def test_migration_creates_tables(tmp_path):
    db_path = tmp_path / "migrate.db"
    engine = create_app_engine(f"sqlite+aiosqlite:///{db_path}")
    await run_migrations(engine)

    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        tables = {row[0] for row in result.fetchall()}

    await engine.dispose()
    assert "captures" in tables
    assert "tasks" in tables
    assert "nudges" in tables
    assert "schema_migrations" in tables


@pytest.mark.asyncio
async def test_migration_is_idempotent(tmp_path):
    db_path = tmp_path / "idempotent.db"
    engine = create_app_engine(f"sqlite+aiosqlite:///{db_path}")

    await run_migrations(engine)
    await run_migrations(engine)

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM schema_migrations"))
        count = result.scalar()

    await engine.dispose()
    assert count == 1


@pytest.mark.asyncio
async def test_migration_records_name(tmp_path):
    db_path = tmp_path / "record.db"
    engine = create_app_engine(f"sqlite+aiosqlite:///{db_path}")
    await run_migrations(engine)

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name FROM schema_migrations"))
        names = [row[0] for row in result.fetchall()]

    await engine.dispose()
    assert "001_initial.sql" in names
