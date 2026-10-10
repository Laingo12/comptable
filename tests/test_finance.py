"""Charges, salaires 70/30, prélèvements, caisse FG, associés."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.main import app
from app.models.audit import AuditLog


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(session_owner):
    suffix = uuid.uuid4().hex[:8]
    from app.models.user import User as U
    session_owner.add(U(
        username=f"fin_{suffix}", email=None,
        password_hash=hash_password("fin12345"),
        full_name=f"Fin {suffix}", role="ADMIN", is_active=True,
    ))
    await session_owner.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/login",
                          json={"username": f"fin_{suffix}", "password": "fin12345"})
        return r.json()["access_token"]


async def _mois_id(client, headers, code: str) -> int:
    r = await client.get("/api/v1/mois-scolaires", headers=headers)
    return next(m for m in r.json() if m["code"] == code)["id"]


@pytest.mark.asyncio
async def test_charge_creation_annulation_audit(client, admin_token, session_app):
    headers = {"Authorization": f"Bearer {admin_token}"}
    m_oct = await _mois_id(client, headers, "2026-10")

    # Création
    r = await client.post("/api/v1/charges", json={
        "mois_id": m_oct, "libelle": "JIRAMA octobre",
        "categorie": "VARIABLE", "montant": 45_000,
        "date_operation": "2026-10-12",
    }, headers=headers)
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    assert r.json()["montant"] == 45_000

    # Audit INSERT
    row = (await session_app.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "charges",
            AuditLog.entity_id == str(cid),
            AuditLog.action == "INSERT",
        ).limit(1)
    )).scalar_one_or_none()
    assert row is not None

    # Annulation
    r2 = await client.post(f"/api/v1/charges/{cid}/annuler",
                           json={"motif": "Erreur"}, headers=headers)
    assert r2.status_code == 201, r2.text
    inv = r2.json()
    assert inv["montant"] == -45_000
    assert inv["parent_charge_id"] == cid
    assert inv["mois_id"] == m_oct

    # Double annulation refusée
    r3 = await client.post(f"/api/v1/charges/{cid}/annuler",
                           json={"motif": "Encore"}, headers=headers)
    assert r3.status_code == 400


@pytest.mark.asyncio
async def test_associe_et_prelevement(client, admin_token, session_app):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]

    # Associe
    r = await client.post("/api/v1/associes",
                          json={"nom": f"Associe-{suffix}"}, headers=headers)
    assert r.status_code == 201
    aid = r.json()["id"]

    # Prélèvement
    r2 = await client.post("/api/v1/prelevements", json={
        "associe_id": aid, "type": "RETRAIT", "montant": 50_000,
        "date_prelevement": "2026-10-15",
        "destinataire": "FOURNITURES LUCKAS",
        "motif": "Achat fournitures",
    }, headers=headers)
    assert r2.status_code == 201, r2.text
    pid = r2.json()["id"]

    # Annulation
    r3 = await client.post(f"/api/v1/prelevements/{pid}/annuler",
                           json={"motif": "Doublon"}, headers=headers)
    assert r3.status_code == 201
    inv = r3.json()
    assert inv["montant"] == -50_000
    assert inv["associe_id"] == aid
    assert inv["type"] == "RETRAIT"


@pytest.mark.asyncio
async def test_caisse_fg_annulation_sens_inverse(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    r = await client.post("/api/v1/caisse-fg", json={
        "sens": "ENTREE", "montant": 25_000,
        "libelle": "Recette FG test", "date_operation": "2026-10-05",
    }, headers=headers)
    assert r.status_code == 201
    mid = r.json()["id"]

    r2 = await client.post(f"/api/v1/caisse-fg/{mid}/annuler",
                           json={"motif": "Erreur"}, headers=headers)
    assert r2.status_code == 201, r2.text
    inv = r2.json()
    assert inv["sens"] == "SORTIE"
    assert inv["montant"] == 25_000
    assert inv["parent_mouvement_id"] == mid


@pytest.mark.asyncio
async def test_salaires_generer_et_payer_70_30(client, admin_token, session_app):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]

    # Création d'un employé via ORM direct, commit pour qu'il soit visible
    # par la session des endpoints API (session différente).
    from app.models.personnel import Employe
    from sqlalchemy import select as sa_select

    existing = await session_app.scalar(
        sa_select(Employe).where(Employe.nom == f"Emp{suffix}")
    )
    if existing is None:
        e = Employe(
            nom=f"Emp{suffix}", prenom="Test", poste="Prof",
            salaire_mensuel=200_000, statut="ACTIF",
        )
        session_app.add(e)
        await session_app.commit()
        employe_id = e.id
    else:
        employe_id = existing.id

    m_oct = await _mois_id(client, headers, "2026-10")

    # Génère la ligne salaire mensuelle (idempotent)
    r = await client.post("/api/v1/salaires-mensuels/generer",
                          json={"mois_id": m_oct}, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["created"] >= 1

    # Récupère la ligne de l'employé
    r2 = await client.get(
        f"/api/v1/salaires-mensuels?mois_id={m_oct}", headers=headers
    )
    ligne = next(x for x in r2.json() if x["employe_id"] == employe_id)
    sid = ligne["id"]
    brut = ligne["montant_brut"]
    assert brut == 200_000

    # Avance 70 %
    avance = (brut * 70) // 100
    r3 = await client.post("/api/v1/paiements-salaires", json={
        "salaire_mensuel_id": sid, "type_part": "AVANCE_70",
        "montant": avance, "date_paiement": "2026-10-25",
    }, headers=headers)
    assert r3.status_code == 201, r3.text
    pid = r3.json()["id"]

    # Solde 30 %
    solde = brut - avance
    r4 = await client.post("/api/v1/paiements-salaires", json={
        "salaire_mensuel_id": sid, "type_part": "SOLDE_30",
        "montant": solde, "date_paiement": "2026-11-10",
    }, headers=headers)
    assert r4.status_code == 201, r4.text

    # Cumul dépassant le brut → refus
    r5 = await client.post("/api/v1/paiements-salaires", json={
        "salaire_mensuel_id": sid, "type_part": "SOLDE_30",
        "montant": 1, "date_paiement": "2026-11-10",
    }, headers=headers)
    assert r5.status_code == 400
    assert "dépasse" in r5.json()["detail"]

    # Annulation de l'avance
    r6 = await client.post(
        f"/api/v1/paiements-salaires/{pid}/annuler",
        json={"motif": "Erreur"}, headers=headers,
    )
    assert r6.status_code == 201
    assert r6.json()["montant"] == -avance