"""Fixtures pytest : engines, sessions, helpers."""

from __future__ import annotations

import os

# Doit précéder TOUT import de app.* pour que Settings lise APP_ENV=test.
os.environ["APP_ENV"] = "test"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.models.parametres import AnneeScolaire  # noqa: E402
from app.models.referentiel import (  # noqa: E402
    MoisScolaire,
    ModePaiement,
    Niveau,
    TypePaiement,
)
from app.models.user import User  # noqa: E402


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest_asyncio.fixture
async def session_app(settings):
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
        try:
            await s.rollback()
        except Exception:
            pass
    await engine.dispose()


@pytest_asyncio.fixture
async def session_owner(settings):
    engine = create_async_engine(settings.database_owner_url, poolclass=NullPool)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
        try:
            await s.rollback()
        except Exception:
            pass
    await engine.dispose()


async def get_id(session: AsyncSession, model, **where) -> int:
    stmt = select(model.id)
    for k, v in where.items():
        stmt = stmt.where(getattr(model, k) == v)
    val = await session.scalar(stmt.limit(1))
    assert val is not None, f"{model.__name__} introuvable pour {where}"
    return val


async def annee_id(session) -> int:
    return await get_id(session, AnneeScolaire, is_active=True)


async def mois_id(session, code: str) -> int:
    return await get_id(session, MoisScolaire, code=code)


async def niveau_id(session, code: str) -> int:
    return await get_id(session, Niveau, code=code)


async def type_paiement_id(session, code: str) -> int:
    return await get_id(session, TypePaiement, code=code)


async def mode_id(session, code: str = "ESPECES") -> int:
    return await get_id(session, ModePaiement, code=code)


async def admin_id(session) -> int:
    return await get_id(session, User, role="ADMIN")


async def associe_id(session, nom: str = "Jessy") -> int:
    from app.models.associes import Associe
    return await get_id(session, Associe, nom=nom)