"""Accès données charges (ledger)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.charges import Charge


class ChargeRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def by_id(self, charge_id: int) -> Charge | None:
        return await self.s.scalar(select(Charge).where(Charge.id == charge_id))

    async def exists_annulation(self, parent_id: int) -> bool:
        row = await self.s.scalar(
            select(Charge.id).where(Charge.parent_charge_id == parent_id).limit(1)
        )
        return row is not None

    async def list(
        self, page, page_size, annee_scolaire_id, mois_id, categorie,
        date_from, date_to, include_annules, order_by,
    ) -> tuple[list[Charge], int]:
        stmt = select(Charge)
        counter = select(func.count(Charge.id))
        conds = []
        if annee_scolaire_id is not None:
            conds.append(Charge.annee_scolaire_id == annee_scolaire_id)
        if mois_id is not None:
            conds.append(Charge.mois_id == mois_id)
        if categorie is not None:
            conds.append(Charge.categorie == categorie)
        if date_from is not None:
            conds.append(Charge.date_operation >= date_from)
        if date_to is not None:
            conds.append(Charge.date_operation <= date_to)
        if not include_annules:
            conds.append(Charge.parent_charge_id.is_(None))
        for c in conds:
            stmt = stmt.where(c)
            counter = counter.where(c)
        total = (await self.s.execute(counter)).scalar_one()
        rows = (await self.s.execute(
            stmt.order_by(*order_by).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        return list(rows), total

    async def create(self, **fields) -> Charge:
        obj = Charge(**fields)
        self.s.add(obj)
        await self.s.flush()
        return obj