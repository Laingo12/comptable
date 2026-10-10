"""Service paiements : règles métier et annulation (écriture inverse)."""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eleves import Inscription
from app.models.paiements import Paiement
from app.models.referentiel import TypePaiement
from app.repositories.paiements import PaiementRepository


class PaiementError(Exception):
    """Erreur métier sur les paiements."""


async def _code_type(session: AsyncSession, type_paiement_id: int) -> str | None:
    return await session.scalar(
        __import__("sqlalchemy").select(TypePaiement.code).where(
            TypePaiement.id == type_paiement_id
        )
    )


async def create(
    session: AsyncSession, *, created_by: int, data: dict
) -> Paiement:
    inscription_id = data.get("inscription_id")
    type_paiement_id = data["type_paiement_id"]
    mois_concerne_id = data.get("mois_concerne_id")

    code = await _code_type(session, type_paiement_id)
    if code is None:
        raise PaiementError("Type de paiement inconnu")

    # Détermine l'année scolaire : via inscription si présente, sinon via un paramètre.
    annee_scolaire_id = None
    if inscription_id is not None:
        ins = await session.scalar(
            __import__("sqlalchemy").select(Inscription).where(
                Inscription.id == inscription_id
            )
        )
        if ins is None:
            raise PaiementError("Inscription introuvable")
        annee_scolaire_id = ins.annee_scolaire_id

    if annee_scolaire_id is None:
        raise PaiementError(
            "inscription_id obligatoire (l'année scolaire est déduite de l'inscription)"
        )

    # Règles par type
    if code == "ECOLAGE":
        if mois_concerne_id is None:
            raise PaiementError("mois_concerne_id obligatoire pour un écolage")
    elif code in ("INSCRIPTION", "FRAIS_GENERAUX"):
        # Une seule ligne par inscription suffit : on autorise plusieurs versements
        # mais on n'exige pas de mois.
        if inscription_id is None:
            raise PaiementError(f"inscription_id obligatoire pour un paiement {code}")
    elif code == "AUTRE":
        # Autorisé sans inscription ; l'année scolaire est alors obligatoire
        annee_scolaire_id = data.get("annee_scolaire_id") or annee_scolaire_id
        if annee_scolaire_id is None:
            raise PaiementError("annee_scolaire_id obligatoire pour un paiement AUTRE")

    # Cohérence date / date_a_completer
    date_p = data.get("date_paiement")
    date_a_completer = data.get("date_a_completer", False)
    if not date_a_completer and date_p is None:
        date_p = date.today()

    fields = {
        "annee_scolaire_id": annee_scolaire_id,
        "inscription_id": inscription_id,
        "type_paiement_id": type_paiement_id,
        "mois_concerne_id": mois_concerne_id,
        "montant": data["montant"],
        "date_paiement": None if date_a_completer else date_p,
        "date_a_completer": date_a_completer,
        "mode_paiement_id": data.get("mode_paiement_id"),
        "reference": data.get("reference"),
        "observation": data.get("observation"),
        "created_by": created_by,
    }
    return await PaiementRepository(session).create(**fields)


async def annuler(
    session: AsyncSession, *, paiement_id: int, created_by: int, motif: str
) -> Paiement:
    repo = PaiementRepository(session)
    original = await repo.by_id(paiement_id)
    if original is None:
        raise PaiementError("Paiement introuvable")
    if original.parent_paiement_id is not None:
        raise PaiementError("Impossible d'annuler une annulation")
    if await repo.exists_annulation(original.id):
        raise PaiementError("Paiement déjà annulé")

    inverse = await repo.create(
        annee_scolaire_id=original.annee_scolaire_id,
        inscription_id=original.inscription_id,
        type_paiement_id=original.type_paiement_id,
        mois_concerne_id=original.mois_concerne_id,
        montant=-original.montant,
        date_paiement=date.today(),
        date_a_completer=False,
        mode_paiement_id=original.mode_paiement_id,
        reference=original.reference,
        observation=f"Annulation du paiement #{original.id}",
        parent_paiement_id=original.id,
        motif_annulation=motif,
        created_by=created_by,
    )
    return inverse