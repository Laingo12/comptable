"""Accès données paiements (ledger)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paiements import Paiement


class PaiementRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def by_id(self, paiement_id: int) -> Paiement | None:
        return await self.s.scalar(
            select(Paiement).where(Paiement.id == paiement_id)
        )

    async def list(
        self,
        page: int,
        page_size: int,
        annee_scolaire_id: int | None,
        inscription_id: int | None,
        type_paiement_id: int | None,
        mois_concerne_id: int | None,
        date_from,
        date_to,
        include_annules: bool,
        order_by,
    ) -> tuple[list[Paiement], int]:
        stmt = select(Paiement)
        counter = select(func.count(Paiement.id))
        conditions = []
        if annee_scolaire_id is not None:
            conditions.append(Paiement.annee_scolaire_id == annee_scolaire_id)
        if inscription_id is not None:
            conditions.append(Paiement.inscription_id == inscription_id)
        if type_paiement_id is not None:
            conditions.append(Paiement.type_paiement_id == type_paiement_id)
        if mois_concerne_id is not None:
            conditions.append(Paiement.mois_concerne_id == mois_concerne_id)
        if date_from is not None:
            conditions.append(Paiement.date_paiement >= date_from)
        if date_to is not None:
            conditions.append(Paiement.date_paiement <= date_to)
        if not include_annules:
            conditions.append(Paiement.parent_paiement_id.is_(None))
        for c in conditions:
            stmt = stmt.where(c)
            counter = counter.where(c)
        total = (await self.s.execute(counter)).scalar_one()
        rows = (await self.s.execute(
            stmt.order_by(*order_by)
            .offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        return list(rows), total

    async def create(self, **fields) -> Paiement:
        obj = Paiement(**fields)
        self.s.add(obj)
        await self.s.flush()
        return obj

    async def exists_annulation(self, parent_id: int) -> bool:
        row = await self.s.scalar(
            select(Paiement.id).where(Paiement.parent_paiement_id == parent_id).limit(1)
        )
        return row is not None