"""SQLAlchemy base and async session factory."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config import load_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        settings = load_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(_get_engine(), expire_on_commit=False)
    return _session_factory


async def get_session() -> AsyncSession:
    async with _get_session_factory()() as session:
        yield session


async def init_db() -> None:
    from backend.models import asset, evaluation, job, persona, project, user  # noqa: F401

    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
