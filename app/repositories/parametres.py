"""Accès données paramètres versionnés."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parametres import Parametre


class ParametreRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def list(self, annee_scolaire_id: int) -> list[Parametre]:
        return list((await self.s.scalars(
            select(Parametre)
            .where(Parametre.annee_scolaire_id == annee_scolaire_id)
            .order_by(Parametre.cle)
        )).all())

    async def get(self, annee_scolaire_id: int, cle: str) -> Parametre | None:
        return await self.s.scalar(
            select(Parametre).where(
                Parametre.annee_scolaire_id == annee_scolaire_id,
                Parametre.cle == cle,
            )
        )

    async def upsert(
        self,
        annee_scolaire_id: int,
        cle: str,
        valeur,
        description: str | None,
        updated_by: int,
    ) -> Parametre:
        obj = await self.get(annee_scolaire_id, cle)
        if obj is None:
            obj = Parametre(
                annee_scolaire_id=annee_scolaire_id,
                cle=cle,
                valeur=valeur,
                description=description,
                updated_by=updated_by,
            )
            self.s.add(obj)
        else:
            obj.valeur = valeur
            if description is not None:
                obj.description = description
            obj.updated_by = updated_by
        await self.s.flush()
        return obj