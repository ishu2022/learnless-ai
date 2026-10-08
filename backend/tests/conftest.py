import os

# Dummy values so Settings() loads without a real .env. Set BEFORE importing the app.
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("MINIO_ROOT_USER", "test")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "testtest")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.refresh_token import RefreshToken  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401

# Auth tests ONLY ever talk to this database, never to the dev database.
TEST_DB_NAME = "learnless_test"
_TRUNCATE_SQL = "TRUNCATE TABLE refresh_tokens, users RESTART IDENTITY CASCADE"


async def _fake_db():
    yield None


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = _fake_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def db_engine():
    """Engine for the separate test database, with empty tables for each test."""
    url = get_settings().database_url.set(database=TEST_DB_NAME)
    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(_TRUNCATE_SQL))
    yield engine
    async with engine.begin() as conn:
        await conn.execute(text(_TRUNCATE_SQL))
    await engine.dispose()


@pytest.fixture
async def db_client(db_engine):
    """HTTP test client whose requests use the real test database."""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()