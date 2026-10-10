"""Service prélèvements : création + annulation (écriture inverse)."""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prelevements import Prelevement
from app.repositories.prelevements import PrelevementRepository
from app.repositories.referentiels import ReferentielRepository


class PrelevementError(Exception):
    pass


async def create(
    session: AsyncSession, *, created_by: int, data: dict
) -> Prelevement:
    annee = await ReferentielRepository(session).get_annee_active()
    if annee is None:
        raise PrelevementError("Aucune année scolaire active")

    date_a_completer = data.get("date_a_completer", False)
    date_p = data.get("date_prelevement")
    if not date_a_completer and date_p is None:
        date_p = date.today()

    return await PrelevementRepository(session).create(
        annee_scolaire_id=annee.id,
        associe_id=data["associe_id"],
        type=data["type"],
        montant=data["montant"],
        date_prelevement=None if date_a_completer else date_p,
        date_a_completer=date_a_completer,
        destinataire=data.get("destinataire"),
        motif=data.get("motif"),
        mode_paiement_id=data.get("mode_paiement_id"),
        reference=data.get("reference"),
        created_by=created_by,
    )


async def annuler(
    session: AsyncSession, *, prelevement_id: int, created_by: int, motif: str
) -> Prelevement:
    repo = PrelevementRepository(session)
    original = await repo.by_id(prelevement_id)
    if original is None:
        raise PrelevementError("Prélèvement introuvable")
    if original.parent_prelevement_id is not None:
        raise PrelevementError("Impossible d'annuler une annulation")
    if await repo.exists_annulation(original.id):
        raise PrelevementError("Prélèvement déjà annulé")
    return await repo.create(
        annee_scolaire_id=original.annee_scolaire_id,
        associe_id=original.associe_id,
        type=original.type,
        montant=-original.montant,
        date_prelevement=date.today(),
        date_a_completer=False,
        destinataire=original.destinataire,
        motif=f"Annulation du prélèvement #{original.id} : {motif}",
        mode_paiement_id=original.mode_paiement_id,
        reference=original.reference,
        parent_prelevement_id=original.id,
        created_by=created_by,
    )