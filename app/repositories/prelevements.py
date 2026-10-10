"""Accès données prélèvements (ledger)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prelevements import Prelevement


class PrelevementRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def by_id(self, pid: int) -> Prelevement | None:
        return await self.s.scalar(select(Prelevement).where(Prelevement.id == pid))

    async def exists_annulation(self, parent_id: int) -> bool:
        row = await self.s.scalar(
            select(Prelevement.id)
            .where(Prelevement.parent_prelevement_id == parent_id).limit(1)
        )
        return row is not None

    async def list(
        self, page, page_size, annee_scolaire_id, associe_id, mois_id, type_,
        date_from, date_to, include_annules, order_by,
    ) -> tuple[list[Prelevement], int]:
        stmt = select(Prelevement)
        counter = select(func.count(Prelevement.id))
        conds = []
        if annee_scolaire_id is not None:
            conds.append(Prelevement.annee_scolaire_id == annee_scolaire_id)
        if associe_id is not None:
            conds.append(Prelevement.associe_id == associe_id)
        if mois_id is not None:
            conds.append(Prelevement.mois_id == mois_id)
        if type_ is not None:
            conds.append(Prelevement.type == type_)
        if date_from is not None:
            conds.append(Prelevement.date_prelevement >= date_from)
        if date_to is not None:
            conds.append(Prelevement.date_prelevement <= date_to)
        if not include_annules:
            conds.append(Prelevement.parent_prelevement_id.is_(None))
        for c in conds:
            stmt = stmt.where(c)
            counter = counter.where(c)
        total = (await self.s.execute(counter)).scalar_one()
        rows = (await self.s.execute(
            stmt.order_by(*order_by).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        return list(rows), total

    async def create(self, **fields) -> Prelevement:
        obj = Prelevement(**fields)
        self.s.add(obj)
        await self.s.flush()
        return obj