"""Accès données élèves et inscriptions."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eleves import Eleve, Inscription


class EleveRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def by_id(self, eleve_id: int) -> Eleve | None:
        return await self.s.scalar(select(Eleve).where(Eleve.id == eleve_id))

    async def by_matricule(self, matricule: str) -> Eleve | None:
        return await self.s.scalar(select(Eleve).where(Eleve.matricule == matricule))

    async def next_matricule(self, annee_debut: int) -> str:
        prefix = f"SK-{annee_debut}-"
        last = await self.s.scalar(
            select(func.max(Eleve.matricule)).where(Eleve.matricule.like(prefix + "%"))
        )
        if last is None:
            n = 1
        else:
            n = int(last[len(prefix):]) + 1
        return f"{prefix}{n:04d}"

    async def list(
        self,
        page: int,
        page_size: int,
        q: str | None,
        famille_id: int | None,
        order_by,
    ) -> tuple[list[Eleve], int]:
        stmt = select(Eleve)
        counter = select(func.count(Eleve.id))
        if famille_id is not None:
            stmt = stmt.where(Eleve.famille_id == famille_id)
            counter = counter.where(Eleve.famille_id == famille_id)
        if q:
            like = f"%{q.lower()}%"
            cond = or_(
                func.lower(Eleve.nom).like(like),
                func.lower(Eleve.prenoms).like(like),
                func.lower(Eleve.matricule).like(like),
            )
            stmt = stmt.where(cond)
            counter = counter.where(cond)
        total = (await self.s.execute(counter)).scalar_one()
        rows = (await self.s.execute(
            stmt.order_by(*order_by).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        return list(rows), total

    async def create(self, **fields) -> Eleve:
        obj = Eleve(**fields)
        self.s.add(obj)
        await self.s.flush()
        return obj


class InscriptionRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def by_id(self, inscription_id: int) -> Inscription | None:
        return await self.s.scalar(
            select(Inscription).where(Inscription.id == inscription_id)
        )

    async def by_eleve_annee(self, eleve_id: int, annee_scolaire_id: int) -> Inscription | None:
        return await self.s.scalar(
            select(Inscription).where(
                Inscription.eleve_id == eleve_id,
                Inscription.annee_scolaire_id == annee_scolaire_id,
            )
        )

    async def list(
        self,
        page: int,
        page_size: int,
        annee_scolaire_id: int | None,
        niveau_id: int | None,
        statut: str | None,
        eleve_id: int | None,
        order_by,
    ) -> tuple[list[Inscription], int]:
        stmt = select(Inscription)
        counter = select(func.count(Inscription.id))
        if annee_scolaire_id is not None:
            stmt = stmt.where(Inscription.annee_scolaire_id == annee_scolaire_id)
            counter = counter.where(Inscription.annee_scolaire_id == annee_scolaire_id)
        if niveau_id is not None:
            stmt = stmt.where(Inscription.niveau_id == niveau_id)
            counter = counter.where(Inscription.niveau_id == niveau_id)
        if statut is not None:
            stmt = stmt.where(Inscription.statut == statut)
            counter = counter.where(Inscription.statut == statut)
        if eleve_id is not None:
            stmt = stmt.where(Inscription.eleve_id == eleve_id)
            counter = counter.where(Inscription.eleve_id == eleve_id)
        total = (await self.s.execute(counter)).scalar_one()
        rows = (await self.s.execute(
            stmt.order_by(*order_by).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        return list(rows), total

    async def active_eleve_ids_of_famille(
        self, famille_id: int, annee_scolaire_id: int
    ) -> list[int]:
        rows = (await self.s.execute(
            select(Inscription.id)
            .join(Eleve, Eleve.id == Inscription.eleve_id)
            .where(
                Eleve.famille_id == famille_id,
                Inscription.annee_scolaire_id == annee_scolaire_id,
                Inscription.statut == "ACTIF",
            )
        )).scalars().all()
        return list(rows)

    async def list_of_famille(
        self, famille_id: int, annee_scolaire_id: int
    ) -> list[Inscription]:
        rows = (await self.s.execute(
            select(Inscription)
            .join(Eleve, Eleve.id == Inscription.eleve_id)
            .where(
                Eleve.famille_id == famille_id,
                Inscription.annee_scolaire_id == annee_scolaire_id,
            )
        )).scalars().all()
        return list(rows)

    async def create(self, **fields) -> Inscription:
        obj = Inscription(**fields)
        self.s.add(obj)
        await self.s.flush()
        return obj