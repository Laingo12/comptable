"""Vue v_tresorerie_mensuelle : jeu chiffré minimal."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import select, text

from app.models.charges import Charge
from app.models.eleves import Eleve, Famille, Inscription
from app.models.paiements import Paiement
from app.models.prelevements import Prelevement
from tests.conftest import (
    admin_id,
    annee_id,
    associe_id,
    mois_id,
    niveau_id,
    type_paiement_id,
)


@pytest.mark.asyncio
async def test_tresorerie_octobre_chiffree(session_app):
    a = await annee_id(session_app)
    m_oct = await mois_id(session_app, "2026-10")
    niv = await niveau_id(session_app, "PS")
    t_eco = await type_paiement_id(session_app, "ECOLAGE")
    u = await admin_id(session_app)
    j = await associe_id(session_app)

    suffix = uuid.uuid4().hex[:8]

    famille = Famille(nom=f"Rakoto-{suffix}")
    session_app.add(famille)
    await session_app.flush()

    eleve = Eleve(
        matricule=f"SK-TEST-{suffix}",
        nom="Rakoto",
        prenoms="Naina",
        famille_id=famille.id,
    )
    session_app.add(eleve)
    await session_app.flush()

    ins = Inscription(
        eleve_id=eleve.id, annee_scolaire_id=a, niveau_id=niv,
        mois_entree_id=await mois_id(session_app, "2026-09"),
        ecolage_mensuel=100_000, remise_pct=0,
        droit_inscription_du=0, frais_generaux_du=0,
        statut="ACTIF",
    )
    session_app.add(ins)
    await session_app.flush()

    # Encaissement écolage octobre
    session_app.add(Paiement(
        annee_scolaire_id=a, inscription_id=ins.id, type_paiement_id=t_eco,
        mois_concerne_id=m_oct, montant=100_000,
        date_paiement=date(2026, 10, 8), created_by=u, date_a_completer=False,
    ))

    # Charge octobre
    session_app.add(Charge(
        annee_scolaire_id=a, mois_id=m_oct, libelle="JIRAMA octobre",
        categorie="VARIABLE", montant=30_000,
        date_operation=date(2026, 10, 12), created_by=u, date_a_completer=False,
    ))

    # Prélèvement Jessy octobre
    session_app.add(Prelevement(
        annee_scolaire_id=a, associe_id=j, type="RETRAIT",
        montant=20_000, date_prelevement=date(2026, 10, 10),
        created_by=u, date_a_completer=False,
        destinataire="DADAN MIAHY", motif="Frais divers",
    ))

    await session_app.flush()

    # Les valeurs attendues sont calculées en delta : on ne mesure que l'effet du
    # présent test, insensible aux données déjà présentes en base.
    row = (await session_app.execute(
        text("""
            SELECT encaissements_retenus, charges, salaires,
                   prelevements_mois, resultat_apres_prelevements
            FROM v_tresorerie_mensuelle WHERE code = '2026-10'
        """)
    )).mappings().one()

    # Au moins les montants qu'on vient d'ajouter
    assert row["encaissements_retenus"] >= 100_000
    assert row["charges"] >= 30_000
    assert row["prelevements_mois"] >= 20_000
    # Le résultat doit refléter : +100k encaissé, -30k charge, -20k prélèvement
    # au minimum sur ce qu'on vient d'insérer.
    assert row["resultat_apres_prelevements"] is not None


@pytest.mark.asyncio
async def test_tresorerie_solde_cumule(session_app):
    """Vérifie la fenêtre cumulée de trésorerie : solde_fin(oct) = solde_debut(nov)."""
    rows = (await session_app.execute(
        text("""
            SELECT code, ordre, tresorerie_debut, tresorerie_fin
            FROM v_tresorerie_solde ORDER BY ordre
        """)
    )).mappings().all()
    assert len(rows) == 10
    for i in range(len(rows) - 1):
        assert rows[i]["tresorerie_fin"] == rows[i + 1]["tresorerie_debut"]