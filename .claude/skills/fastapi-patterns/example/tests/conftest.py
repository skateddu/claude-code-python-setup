"""Fixtures: an app on a fresh in-memory database for every test."""

from collections.abc import AsyncIterator

from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from my_app.config import Settings
from my_app.database import Base
from my_app.main import create_app

TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL,
        jwt_secret_key="test-only-secret-key-of-at-least-32-bytes",
    )


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    # One engine per test, so each test starts on an empty database.
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def client(settings: Settings, engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    app = create_app(settings=settings, engine=engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
