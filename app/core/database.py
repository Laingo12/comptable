"""Base SQLAlchemy 2.x async : engine, sessionmaker, dépendance FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from app.core.config import get_settings
from app.models.base import Base  # noqa: F401  — ré-exporté pour compat

_settings = get_settings()

if _settings.app_env.lower() in {"test", "testing"}:
    engine: AsyncEngine = create_async_engine(
        _settings.database_url,
        echo=False,
        poolclass=NullPool,
        future=True,
    )
else:
    engine = create_async_engine(
        _settings.database_url,
        echo=False,
        pool_pre_ping=True,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=10,
        max_overflow=20,
        future=True,
    )

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dépendance FastAPI : fournit une session par requête."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise