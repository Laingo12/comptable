"""Accès données référentiels et années scolaires."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parametres import (
    AnneeScolaire,
    ChargeCatalogue,
    GrilleTarifaire,
)
from app.models.referentiel import (
    MoisScolaire,
    ModePaiement,
    Niveau,
    TypePaiement,
)


class ReferentielRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def list_niveaux(self) -> list[Niveau]:
        return list((await self.s.scalars(
            select(Niveau).order_by(Niveau.ordre)
        )).all())

    async def list_mois(self, annee_scolaire_id: int) -> list[MoisScolaire]:
        return list((await self.s.scalars(
            select(MoisScolaire)
            .where(MoisScolaire.annee_scolaire_id == annee_scolaire_id)
            .order_by(MoisScolaire.ordre)
        )).all())

    async def list_types(self) -> list[TypePaiement]:
        return list((await self.s.scalars(
            select(TypePaiement).order_by(TypePaiement.ordre)
        )).all())

    async def list_modes(self) -> list[ModePaiement]:
        return list((await self.s.scalars(
            select(ModePaiement).order_by(ModePaiement.ordre)
        )).all())

    async def list_annees(self) -> list[AnneeScolaire]:
        return list((await self.s.scalars(
            select(AnneeScolaire).order_by(AnneeScolaire.date_debut.desc())
        )).all())

    async def get_annee_active(self) -> AnneeScolaire | None:
        return await self.s.scalar(
            select(AnneeScolaire).where(AnneeScolaire.is_active.is_(True)).limit(1)
        )

    async def list_grille(self, annee_scolaire_id: int) -> list[GrilleTarifaire]:
        return list((await self.s.scalars(
            select(GrilleTarifaire)
            .where(GrilleTarifaire.annee_scolaire_id == annee_scolaire_id)
            .order_by(GrilleTarifaire.niveau_id)
        )).all())

    async def get_grille(self, annee_scolaire_id: int, niveau_id: int) -> GrilleTarifaire | None:
        return await self.s.scalar(
            select(GrilleTarifaire).where(
                GrilleTarifaire.annee_scolaire_id == annee_scolaire_id,
                GrilleTarifaire.niveau_id == niveau_id,
            )
        )

    async def list_charges(self, annee_scolaire_id: int | None = None) -> list[ChargeCatalogue]:
        stmt = select(ChargeCatalogue).order_by(ChargeCatalogue.libelle)
        if annee_scolaire_id is not None:
            stmt = stmt.where(
                (ChargeCatalogue.annee_scolaire_id == annee_scolaire_id)
                | (ChargeCatalogue.annee_scolaire_id.is_(None))
            )
        return list((await self.s.scalars(stmt)).all())

    async def get_charge(self, charge_id: int) -> ChargeCatalogue | None:
        return await self.s.scalar(
            select(ChargeCatalogue).where(ChargeCatalogue.id == charge_id)
        )