"""Service caisse FG : création + annulation (mouvement inverse)."""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.caisse_fg import CaisseFgMouvement
from app.repositories.caisse_fg import CaisseFgRepository
from app.repositories.referentiels import ReferentielRepository


class CaisseFgError(Exception):
    pass


async def create(
    session: AsyncSession, *, created_by: int, data: dict
) -> CaisseFgMouvement:
    annee = await ReferentielRepository(session).get_annee_active()
    if annee is None:
        raise CaisseFgError("Aucune année scolaire active")

    date_a_completer = data.get("date_a_completer", False)
    date_p = data.get("date_operation")
    if not date_a_completer and date_p is None:
        date_p = date.today()

    return await CaisseFgRepository(session).create(
        annee_scolaire_id=annee.id,
        sens=data["sens"],
        montant=data["montant"],
        date_operation=None if date_a_completer else date_p,
        date_a_completer=date_a_completer,
        libelle=data["libelle"],
        remarque=data.get("remarque"),
        mode_paiement_id=data.get("mode_paiement_id"),
        reference=data.get("reference"),
        created_by=created_by,
    )

async def annuler(
    session: AsyncSession, *, mouvement_id: int, created_by: int, motif: str
) -> CaisseFgMouvement:
    repo = CaisseFgRepository(session)
    original = await repo.by_id(mouvement_id)
    if original is None:
        raise CaisseFgError("Mouvement introuvable")
    if original.parent_mouvement_id is not None:
        raise CaisseFgError("Impossible d'annuler une annulation")
    if await repo.exists_annulation(original.id):
        raise CaisseFgError("Mouvement déjà annulé")

    sens_inverse = "SORTIE" if original.sens == "ENTREE" else "ENTREE"
    return await repo.create(
        annee_scolaire_id=original.annee_scolaire_id,
        mois_id=original.mois_id,           # ← vérifié par le trigger d'annulation
        sens=sens_inverse,
        montant=original.montant,
        date_operation=date.today(),
        date_a_completer=False,
        libelle=f"Annulation du mouvement #{original.id} : {motif}",
        remarque=original.remarque,
        mode_paiement_id=original.mode_paiement_id,
        reference=original.reference,
        parent_mouvement_id=original.id,
        created_by=created_by,
    )