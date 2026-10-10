"""Accès données salaires mensuels et paiements de salaires."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.personnel import SalaireMensuel
from app.models.salaires import PaiementSalaire


class SalaireMensuelRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def by_id(self, sid: int) -> SalaireMensuel | None:
        return await self.s.scalar(
            select(SalaireMensuel).where(SalaireMensuel.id == sid)
        )

    async def by_employe_mois(self, employe_id: int, mois_id: int) -> SalaireMensuel | None:
        return await self.s.scalar(
            select(SalaireMensuel).where(
                SalaireMensuel.employe_id == employe_id,
                SalaireMensuel.mois_id == mois_id,
            )
        )

    async def list(self, annee_scolaire_id, mois_id, order_by):
        stmt = select(SalaireMensuel)
        if annee_scolaire_id is not None:
            stmt = stmt.where(SalaireMensuel.annee_scolaire_id == annee_scolaire_id)
        if mois_id is not None:
            stmt = stmt.where(SalaireMensuel.mois_id == mois_id)
        stmt = stmt.order_by(*order_by)
        return list((await self.s.scalars(stmt)).all())

    async def create(self, **fields) -> SalaireMensuel:
        obj = SalaireMensuel(**fields)
        self.s.add(obj)
        await self.s.flush()
        return obj


class PaiementSalaireRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def by_id(self, pid: int) -> PaiementSalaire | None:
        return await self.s.scalar(
            select(PaiementSalaire).where(PaiementSalaire.id == pid)
        )

    async def exists_annulation(self, parent_id: int) -> bool:
        row = await self.s.scalar(
            select(PaiementSalaire.id)
            .where(PaiementSalaire.parent_paiement_salaire_id == parent_id)
            .limit(1)
        )
        return row is not None

    async def list(
        self, page, page_size, annee_scolaire_id, employe_id, salaire_mensuel_id,
        include_annules, order_by,
    ) -> tuple[list[PaiementSalaire], int]:
        stmt = select(PaiementSalaire)
        counter = select(func.count(PaiementSalaire.id))
        conds = []
        if annee_scolaire_id is not None:
            conds.append(PaiementSalaire.annee_scolaire_id == annee_scolaire_id)
        if employe_id is not None:
            conds.append(PaiementSalaire.employe_id == employe_id)
        if salaire_mensuel_id is not None:
            conds.append(PaiementSalaire.salaire_mensuel_id == salaire_mensuel_id)
        if not include_annules:
            conds.append(PaiementSalaire.parent_paiement_salaire_id.is_(None))
        for c in conds:
            stmt = stmt.where(c)
            counter = counter.where(c)
        total = (await self.s.execute(counter)).scalar_one()
        rows = (await self.s.execute(
            stmt.order_by(*order_by).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        return list(rows), total

    async def create(self, **fields) -> PaiementSalaire:
        obj = PaiementSalaire(**fields)
        self.s.add(obj)
        await self.s.flush()
        return obj