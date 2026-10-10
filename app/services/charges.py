"""Service charges : création + annulation."""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.charges import Charge
from app.repositories.charges import ChargeRepository
from app.repositories.referentiels import ReferentielRepository


class ChargeError(Exception):
    pass


async def create(
    session: AsyncSession, *, created_by: int, data: dict
) -> Charge:
    annee = await ReferentielRepository(session).get_annee_active()
    if annee is None:
        raise ChargeError("Aucune année scolaire active")

    date_a_completer = data.get("date_a_completer", False)
    date_p = data.get("date_operation")
    if not date_a_completer and date_p is None:
        date_p = date.today()

    return await ChargeRepository(session).create(
        annee_scolaire_id=annee.id,
        charge_catalogue_id=data.get("charge_catalogue_id"),
        libelle=data["libelle"],
        categorie=data["categorie"],
        montant=data["montant"],
        date_operation=None if date_a_completer else date_p,
        date_a_completer=date_a_completer,
        mode_paiement_id=data.get("mode_paiement_id"),
        reference=data.get("reference"),
        observation=data.get("observation"),
        created_by=created_by,
    )


async def annuler(
    session: AsyncSession, *, charge_id: int, created_by: int, motif: str
) -> Charge:
    repo = ChargeRepository(session)
    original = await repo.by_id(charge_id)
    if original is None:
        raise ChargeError("Charge introuvable")
    if original.parent_charge_id is not None:
        raise ChargeError("Impossible d'annuler une annulation")
    if await repo.exists_annulation(original.id):
        raise ChargeError("Charge déjà annulée")
    return await repo.create(
        annee_scolaire_id=original.annee_scolaire_id,
        mois_id=original.mois_id,
        charge_catalogue_id=original.charge_catalogue_id,
        libelle=f"Annulation de la charge #{original.id} : {motif}",
        categorie=original.categorie,
        montant=-original.montant,
        date_operation=date.today(),
        date_a_completer=False,
        mode_paiement_id=original.mode_paiement_id,
        reference=original.reference,
        observation=original.observation,
        parent_charge_id=original.id,
        created_by=created_by,
    )