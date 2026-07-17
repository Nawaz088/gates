from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from gates.config import settings
from gates.db.base import Base
from gates.db.session import get_session
from gates.main import app

_test_engine = create_async_engine(
    settings.database_test_url,
    echo=False,
)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fresh transactional DB session — skips if Postgres is not running."""
    try:
        async with _test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except OSError:
        pytest.skip("Test database (PostgreSQL) is not available on localhost:5433")

    async with _test_session_factory() as session:
        yield session

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client_with_db(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Test client with `get_session` overridden to use test DB."""
    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
