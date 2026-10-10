"""Service salaires : génération mensuelle + paiements 70/30 + annulation."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.personnel import Employe, SalaireMensuel
from app.models.salaires import PaiementSalaire
from app.repositories.referentiels import ReferentielRepository
from app.repositories.salaires import (
    PaiementSalaireRepository,
    SalaireMensuelRepository,
)


class SalaireError(Exception):
    """Erreur métier salaires."""


async def generer_mensuel(
    session: AsyncSession, *, mois_id: int, annee_scolaire_id: int | None,
    montant_brut_par_defaut: int | None,
) -> dict:
    if annee_scolaire_id is None:
        annee = await ReferentielRepository(session).get_annee_active()
        if annee is None:
            raise SalaireError("Aucune année scolaire active")
        annee_scolaire_id = annee.id

    employes = (await session.execute(
        select(Employe).where(Employe.statut == "ACTIF")
    )).scalars().all()
    repo = SalaireMensuelRepository(session)
    created = 0
    skipped = 0
    for e in employes:
        existing = await repo.by_employe_mois(e.id, mois_id)
        if existing is not None:
            skipped += 1
            continue
        brut = e.salaire_mensuel if montant_brut_par_defaut is None else montant_brut_par_defaut
        await repo.create(
            employe_id=e.id, annee_scolaire_id=annee_scolaire_id,
            mois_id=mois_id, montant_brut=brut,
        )
        created += 1
    return {"created": created, "skipped": skipped, "total": len(employes)}


async def create_paiement(
    session: AsyncSession, *, created_by: int, data: dict
) -> PaiementSalaire:
    sal_id = data["salaire_mensuel_id"]
    sm = await SalaireMensuelRepository(session).by_id(sal_id)
    if sm is None:
        raise SalaireError("Salaire mensuel introuvable")

    type_part = data["type_part"]
    montant = data["montant"]

    # Garde-fou : la somme des paiements du mois ne doit pas dépasser le brut.
    deja = (await session.execute(
        select(PaiementSalaire.montant).where(
            PaiementSalaire.salaire_mensuel_id == sal_id,
            PaiementSalaire.parent_paiement_salaire_id.is_(None),
            ~PaiementSalaire.id.in_(
                select(PaiementSalaire.parent_paiement_salaire_id).where(
                    PaiementSalaire.parent_paiement_salaire_id.is_not(None)
                )
            ),
        )
    )).scalars().all()
    total_paye = sum(int(x) for x in deja)
    if total_paye + montant > int(sm.montant_brut):
        raise SalaireError(
            f"Le cumul des paiements ({total_paye + montant}) dépasse le brut ({sm.montant_brut})"
        )

    date_a_completer = data.get("date_a_completer", False)
    date_p = data.get("date_paiement")
    if not date_a_completer and date_p is None:
        date_p = date.today()

    return await PaiementSalaireRepository(session).create(
        annee_scolaire_id=sm.annee_scolaire_id,
        employe_id=sm.employe_id,
        salaire_mensuel_id=sal_id,
        type_part=type_part,
        montant=montant,
        date_paiement=None if date_a_completer else date_p,
        date_a_completer=date_a_completer,
        mode_paiement_id=data.get("mode_paiement_id"),
        reference=data.get("reference"),
        observation=data.get("observation"),
        created_by=created_by,
    )


async def annuler(
    session: AsyncSession, *, paiement_id: int, created_by: int, motif: str
) -> PaiementSalaire:
    repo = PaiementSalaireRepository(session)
    original = await repo.by_id(paiement_id)
    if original is None:
        raise SalaireError("Paiement salaire introuvable")
    if original.parent_paiement_salaire_id is not None:
        raise SalaireError("Impossible d'annuler une annulation")
    if await repo.exists_annulation(original.id):
        raise SalaireError("Paiement déjà annulé")
    return await repo.create(
        annee_scolaire_id=original.annee_scolaire_id,
        employe_id=original.employe_id,
        salaire_mensuel_id=original.salaire_mensuel_id,
        type_part=original.type_part,
        montant=-original.montant,
        date_paiement=date.today(),
        date_a_completer=False,
        mode_paiement_id=original.mode_paiement_id,
        reference=original.reference,
        observation=f"Annulation du paiement salaire #{original.id} : {motif}",
        parent_paiement_salaire_id=original.id,
        created_by=created_by,
    )