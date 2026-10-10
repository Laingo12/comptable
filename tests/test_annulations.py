"""Cohérence des écritures inverses (annulations)."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import select, text

from app.models.paiements import Paiement
from app.models.prelevements import Prelevement
from tests.conftest import (
    admin_id,
    annee_id,
    associe_id,
    mois_id,
    mode_id,
    type_paiement_id,
)


@pytest.mark.asyncio
async def test_paiement_annulation_ok(session_app):
    a = await annee_id(session_app)
    t = await type_paiement_id(session_app, "AUTRE")
    m = await mode_id(session_app)
    u = await admin_id(session_app)

    orig = Paiement(
        annee_scolaire_id=a, type_paiement_id=t, montant=50_000,
        date_paiement=date(2026, 10, 15), mode_paiement_id=m,
        created_by=u, date_a_completer=False,
    )
    session_app.add(orig)
    await session_app.flush()

    ann = Paiement(
        annee_scolaire_id=a, type_paiement_id=t, montant=-50_000,
        date_paiement=date(2026, 10, 20), mode_paiement_id=m,
        created_by=u, date_a_completer=False,
        parent_paiement_id=orig.id,
    )
    session_app.add(ann)
    await session_app.flush()
    assert ann.id is not None


@pytest.mark.asyncio
async def test_paiement_double_annulation_refusee(session_app):
    a = await annee_id(session_app)
    t = await type_paiement_id(session_app, "AUTRE")
    u = await admin_id(session_app)

    orig = Paiement(
        annee_scolaire_id=a, type_paiement_id=t, montant=10_000,
        date_paiement=date(2026, 10, 15), created_by=u, date_a_completer=False,
    )
    session_app.add(orig)
    await session_app.flush()

    session_app.add(Paiement(
        annee_scolaire_id=a, type_paiement_id=t, montant=-10_000,
        date_paiement=date(2026, 10, 16), created_by=u, date_a_completer=False,
        parent_paiement_id=orig.id,
    ))
    await session_app.flush()

    with pytest.raises(Exception) as exc:
        session_app.add(Paiement(
            annee_scolaire_id=a, type_paiement_id=t, montant=-10_000,
            date_paiement=date(2026, 10, 17), created_by=u, date_a_completer=False,
            parent_paiement_id=orig.id,
        ))
        await session_app.flush()
    msg = str(exc.value).lower()
    assert "duplicate" in msg or "unique" in msg or "uq_paiements_annulation" in msg


@pytest.mark.asyncio
async def test_paiement_annulation_montant_incoherent(session_app):
    a = await annee_id(session_app)
    t = await type_paiement_id(session_app, "AUTRE")
    u = await admin_id(session_app)

    orig = Paiement(
        annee_scolaire_id=a, type_paiement_id=t, montant=10_000,
        date_paiement=date(2026, 10, 15), created_by=u, date_a_completer=False,
    )
    session_app.add(orig)
    await session_app.flush()

    with pytest.raises(Exception) as exc:
        session_app.add(Paiement(
            annee_scolaire_id=a, type_paiement_id=t, montant=-9_000,
            date_paiement=date(2026, 10, 16), created_by=u, date_a_completer=False,
            parent_paiement_id=orig.id,
        ))
        await session_app.flush()
    assert "incohérent" in str(exc.value).lower() or "incoherent" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_prelevement_annulation_copie_mois_du_parent(session_app):
    """Une annulation garde le mois du parent, même si la date d'annulation diffère."""
    a = await annee_id(session_app)
    j = await associe_id(session_app)
    u = await admin_id(session_app)

    orig = Prelevement(
        annee_scolaire_id=a, associe_id=j, type="RETRAIT",
        montant=100_000, date_prelevement=date(2026, 10, 15),
        created_by=u, date_a_completer=False, destinataire="DADAN MIAHY",
    )
    session_app.add(orig)
    await session_app.flush()

    ann = Prelevement(
        annee_scolaire_id=a, associe_id=j, type="RETRAIT",
        montant=-100_000, date_prelevement=date(2026, 12, 20),
        created_by=u, date_a_completer=False,
        parent_prelevement_id=orig.id,
    )
    session_app.add(ann)
    await session_app.flush()

    # Le trigger doit avoir écrasé mois_id par celui du parent
    assert ann.mois_id == orig.mois_id


@pytest.mark.asyncio
async def test_caisse_fg_annulation_meme_sens_refusee(session_app):
    from app.models.caisse_fg import CaisseFgMouvement

    a = await annee_id(session_app)
    u = await admin_id(session_app)
    m = await mois_id(session_app, "2026-10")

    orig = CaisseFgMouvement(
        annee_scolaire_id=a, mois_id=m, sens="ENTREE", montant=5_000,
        date_operation=date(2026, 10, 10), libelle="Encaissement test",
        created_by=u, date_a_completer=False,
    )
    session_app.add(orig)
    await session_app.flush()

    with pytest.raises(Exception) as exc:
        session_app.add(CaisseFgMouvement(
            annee_scolaire_id=a, mois_id=m, sens="ENTREE", montant=5_000,
            date_operation=date(2026, 10, 11), libelle="Annulation mal formée",
            created_by=u, date_a_completer=False,
            parent_mouvement_id=orig.id,
        ))
        await session_app.flush()
    assert "opposé" in str(exc.value).lower() or "oppose" in str(exc.value).lower()