"""Service paramètres : valeurs typées et contrôle d'intégrité."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.parametres import ParametreRepository

# Types attendus par clé (défense contre les valeurs mal typées).
CLE_TYPES: dict[str, type] = {
    "annee_scolaire": str,
    "devise": str,
    "jour_limite_paiement": int,
    "remise_fratrie_pct": int,
    "salaire_avance_pct": int,
    "salaire_solde_pct": int,
    "jour_salaire_avance": int,
    "jour_salaire_solde": int,
    "tresorerie_initiale": int,
    "tresorerie_initiale_date": str,
    "reliquat_salaires_30_precedent": int,
    "inclure_droits_inscription_part_jessy": bool,
    "inclure_frais_generaux_part_jessy": bool,
}

_TYPE_LABELS: dict[type, str] = {
    int: "un entier",
    str: "une chaîne de caractères",
    bool: "un booléen (true/false)",
}


def validate_valeur(cle: str, valeur: Any) -> None:
    expected = CLE_TYPES.get(cle)
    if expected is None:
        return
    if expected is bool:
        if not isinstance(valeur, bool):
            raise ValueError(
                f"Paramètre '{cle}' doit être {_TYPE_LABELS[bool]}"
            )
        return
    if expected is int:
        # bool est sous-classe de int en Python : on refuse explicitement.
        if isinstance(valeur, bool) or not isinstance(valeur, int):
            raise ValueError(
                f"Paramètre '{cle}' doit être {_TYPE_LABELS[int]}"
            )
        return
    if not isinstance(valeur, expected):
        raise ValueError(
            f"Paramètre '{cle}' doit être {_TYPE_LABELS.get(expected, expected.__name__)}"
        )


async def upsert(
    session: AsyncSession,
    annee_scolaire_id: int,
    cle: str,
    valeur: Any,
    description: str | None,
    updated_by: int,
):
    validate_valeur(cle, valeur)
    obj = await ParametreRepository(session).upsert(
        annee_scolaire_id, cle, valeur, description, updated_by
    )
    # Force le rechargement des colonnes server_default / onupdate (updated_at)
    # pour que la sérialisation Pydantic ne déclenche pas de lazy-load async.
    await session.refresh(obj)
    return obj