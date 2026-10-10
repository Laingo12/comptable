"""Service inscriptions : tarif suggéré, remise fratrie, recompute famille."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eleves import Inscription
from app.models.parametres import GrilleTarifaire
from app.repositories.eleves import InscriptionRepository
from app.repositories.parametres import ParametreRepository
from app.repositories.referentiels import ReferentielRepository

CLE_REMISE_FRATRIE = "remise_fratrie_pct"


async def get_remise_fratrie_pct(session: AsyncSession, annee_scolaire_id: int) -> int:
    param = await ParametreRepository(session).get(annee_scolaire_id, CLE_REMISE_FRATRIE)
    if param is None:
        return 0
    try:
        return int(param.valeur)
    except (TypeError, ValueError):
        return 0


async def get_tarif(session: AsyncSession, annee_scolaire_id: int, niveau_id: int) -> GrilleTarifaire | None:
    return await ReferentielRepository(session).get_grille(annee_scolaire_id, niveau_id)


def appliquer_remise(montant: int, pct: int) -> int:
    """Arrondi entier, jamais flottant."""
    if pct <= 0:
        return montant
    return (montant * (100 - pct) + 50) // 100


async def recompute_famille(
    session: AsyncSession, famille_id: int, annee_scolaire_id: int
) -> None:
    """Recalcule remise_pct et écolage_mensuel pour toutes les inscriptions actives
    d'une famille sur une année. Idempotent."""
    repo = InscriptionRepository(session)
    inscriptions = await repo.list_of_famille(famille_id, annee_scolaire_id)
    actifs = [i for i in inscriptions if i.statut == "ACTIF"]
    if not actifs:
        return

    remise_pct = await get_remise_fratrie_pct(session, annee_scolaire_id)
    if len(actifs) < 2:
        remise_pct = 0

    for ins in actifs:
        # Référence tarifaire : valeur de la grille du niveau.
        tarif = await get_tarif(session, annee_scolaire_id, ins.niveau_id)
        if tarif is None:
            continue
        base = tarif.ecolage_mensuel
        ins.remise_pct = remise_pct
        ins.ecolage_mensuel = appliquer_remise(base, remise_pct)
    await session.flush()


async def compute_defaults_for_new(
    session: AsyncSession,
    annee_scolaire_id: int,
    niveau_id: int,
    famille_id: int | None,
) -> dict:
    """Calcule tarif suggéré et remise au moment de la création d'une inscription."""
    tarif = await get_tarif(session, annee_scolaire_id, niveau_id)
    base_eco = tarif.ecolage_mensuel if tarif else 0
    base_insc = tarif.droit_inscription if tarif else 0
    base_fg = tarif.frais_generaux if tarif else 0

    remise_pct = 0
    if famille_id is not None:
        remise_cfg = await get_remise_fratrie_pct(session, annee_scolaire_id)
        actifs = await InscriptionRepository(session).active_eleve_ids_of_famille(
            famille_id, annee_scolaire_id
        )
        # Si au moins 1 autre enfant actif existe, la fratrie s'applique au nouvel entrant.
        if len(actifs) >= 1:
            remise_pct = remise_cfg

    return {
        "ecolage_mensuel": appliquer_remise(base_eco, remise_pct),
        "remise_pct": remise_pct,
        "droit_inscription_du": base_insc,
        "frais_generaux_du": base_fg,
    }