from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config.settings import settings

_engine = create_async_engine(settings.database_url)


@pytest_asyncio.fixture
async def connection() -> AsyncGenerator[AsyncConnection, None]:
    async with _engine.connect() as conn:
        await conn.begin()
        yield conn
        await conn.rollback()


@pytest_asyncio.fixture
async def session(connection: AsyncConnection) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode='create_savepoint',
    ) as db_session:
        yield db_session


@pytest.fixture
def session_factory(connection: AsyncConnection) -> async_sessionmaker[AsyncSession]:
    """Sessions on the test connection: their commits only release a savepoint,
    so the connection rollback at the end still discards everything."""
    return async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode='create_savepoint',
    )
