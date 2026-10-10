"""Accès données associés."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.associes import Associe


class AssocieRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def by_id(self, associe_id: int) -> Associe | None:
        return await self.s.scalar(select(Associe).where(Associe.id == associe_id))

    async def by_nom(self, nom: str) -> Associe | None:
        return await self.s.scalar(select(Associe).where(Associe.nom == nom))

    async def list(self, actif_only: bool = False) -> list[Associe]:
        stmt = select(Associe).order_by(Associe.nom)
        if actif_only:
            stmt = stmt.where(Associe.is_active.is_(True))
        return list((await self.s.scalars(stmt)).all())

    async def create(self, **fields) -> Associe:
        obj = Associe(**fields)
        self.s.add(obj)
        await self.s.flush()
        return obj