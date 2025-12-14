from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base


@lru_cache(maxsize=1)
def get_engine(database_url: str):
    """Create a singleton async engine for the application."""
    return create_async_engine(database_url, echo=False, future=True)


@lru_cache(maxsize=1)
def get_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    engine = get_engine(database_url)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def init_models(database_url: str) -> None:
    """Create database tables for all models if they do not exist."""
    engine = get_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
