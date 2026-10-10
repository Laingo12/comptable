"""Accès données caisse FG (ledger)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.caisse_fg import CaisseFgMouvement


class CaisseFgRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def by_id(self, mid: int) -> CaisseFgMouvement | None:
        return await self.s.scalar(
            select(CaisseFgMouvement).where(CaisseFgMouvement.id == mid)
        )

    async def exists_annulation(self, parent_id: int) -> bool:
        row = await self.s.scalar(
            select(CaisseFgMouvement.id)
            .where(CaisseFgMouvement.parent_mouvement_id == parent_id).limit(1)
        )
        return row is not None

    async def list(
        self, page, page_size, annee_scolaire_id, mois_id, sens,
        date_from, date_to, include_annules, order_by,
    ) -> tuple[list[CaisseFgMouvement], int]:
        stmt = select(CaisseFgMouvement)
        counter = select(func.count(CaisseFgMouvement.id))
        conds = []
        if annee_scolaire_id is not None:
            conds.append(CaisseFgMouvement.annee_scolaire_id == annee_scolaire_id)
        if mois_id is not None:
            conds.append(CaisseFgMouvement.mois_id == mois_id)
        if sens is not None:
            conds.append(CaisseFgMouvement.sens == sens)
        if date_from is not None:
            conds.append(CaisseFgMouvement.date_operation >= date_from)
        if date_to is not None:
            conds.append(CaisseFgMouvement.date_operation <= date_to)
        if not include_annules:
            conds.append(CaisseFgMouvement.parent_mouvement_id.is_(None))
        for c in conds:
            stmt = stmt.where(c)
            counter = counter.where(c)
        total = (await self.s.execute(counter)).scalar_one()
        rows = (await self.s.execute(
            stmt.order_by(*order_by).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        return list(rows), total

    async def create(self, **fields) -> CaisseFgMouvement:
        obj = CaisseFgMouvement(**fields)
        self.s.add(obj)
        await self.s.flush()
        return obj