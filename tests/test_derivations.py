"""Dérivation du mois_id sur prelevements (NON_DATE, HORS_ANNEE, normal)."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import select

from app.models.prelevements import Prelevement
from app.models.referentiel import MoisScolaire
from tests.conftest import admin_id, annee_id, associe_id


async def _mois_code(session, mois_id: int) -> str:
    return await session.scalar(
        select(MoisScolaire.code).where(MoisScolaire.id == mois_id)
    )


@pytest.mark.asyncio
async def test_prelevement_mois_normal(session_app):
    a = await annee_id(session_app)
    j = await associe_id(session_app)
    u = await admin_id(session_app)

    p = Prelevement(
        annee_scolaire_id=a, associe_id=j, type="RETRAIT",
        montant=1_000, date_prelevement=date(2026, 11, 10),
        created_by=u, date_a_completer=False,
    )
    session_app.add(p)
    await session_app.flush()
    assert await _mois_code(session_app, p.mois_id) == "2026-11"


@pytest.mark.asyncio
async def test_prelevement_non_date(session_app):
    a = await annee_id(session_app)
    j = await associe_id(session_app)
    u = await admin_id(session_app)

    p = Prelevement(
        annee_scolaire_id=a, associe_id=j, type="RETRAIT",
        montant=1_000, date_prelevement=None,
        created_by=u, date_a_completer=True,
    )
    session_app.add(p)
    await session_app.flush()
    assert await _mois_code(session_app, p.mois_id) == "NON_DATE"


@pytest.mark.asyncio
async def test_prelevement_hors_annee(session_app):
    a = await annee_id(session_app)
    j = await associe_id(session_app)
    u = await admin_id(session_app)

    p = Prelevement(
        annee_scolaire_id=a, associe_id=j, type="RETRAIT",
        montant=1_000, date_prelevement=date(2027, 8, 15),
        created_by=u, date_a_completer=False,
    )
    session_app.add(p)
    await session_app.flush()
    assert await _mois_code(session_app, p.mois_id) == "HORS_ANNEE"


@pytest.mark.asyncio
async def test_prelevement_date_manquante_refusee(session_app):
    a = await annee_id(session_app)
    j = await associe_id(session_app)
    u = await admin_id(session_app)

    with pytest.raises(Exception) as exc:
        session_app.add(Prelevement(
            annee_scolaire_id=a, associe_id=j, type="RETRAIT",
            montant=1_000, date_prelevement=None,
            created_by=u, date_a_completer=False,
        ))
        await session_app.flush()
    assert "obligatoire" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_paiement_non_date(session_app):
    from app.models.paiements import Paiement
    from tests.conftest import type_paiement_id

    a = await annee_id(session_app)
    t = await type_paiement_id(session_app, "AUTRE")
    u = await admin_id(session_app)

    p = Paiement(
        annee_scolaire_id=a, type_paiement_id=t, montant=1_000,
        date_paiement=None, date_a_completer=True, created_by=u,
    )
    session_app.add(p)
    await session_app.flush()
    # Pas de mois_concerne forcé pour AUTRE ; la date null doit être acceptée
    assert p.id is not None