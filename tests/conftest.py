# ABOUTME: Shared test fixtures — in-memory SQLite database and async HTTP client.
# ABOUTME: Overrides the real DB session so tests never touch disk.
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("CAPTURE_TOKEN", "test-capture-token")
os.environ.setdefault("ADMIN_TOKEN", "test-admin-token")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adhdaf.database import create_app_engine
from adhdaf.models import Base


@pytest.fixture
async def db_engine():
    engine = create_app_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_engine):
    from adhdaf.app import app
    from adhdaf.database import get_session

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
