"""Accès données familles."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eleves import Famille


class FamilleRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def by_id(self, famille_id: int) -> Famille | None:
        return await self.s.scalar(select(Famille).where(Famille.id == famille_id))

    async def list(
        self,
        page: int,
        page_size: int,
        q: str | None,
        order_by,
    ) -> tuple[list[Famille], int]:
        stmt = select(Famille)
        counter = select(func.count(Famille.id))
        if q:
            like = f"%{q.lower()}%"
            cond = or_(
                func.lower(Famille.nom).like(like),
                func.lower(Famille.telephone).like(like),
            )
            stmt = stmt.where(cond)
            counter = counter.where(cond)
        total = (await self.s.execute(counter)).scalar_one()
        rows = (await self.s.execute(
            stmt.order_by(*order_by).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        return list(rows), total

    async def create(self, **fields) -> Famille:
        obj = Famille(**fields)
        self.s.add(obj)
        await self.s.flush()
        return obj