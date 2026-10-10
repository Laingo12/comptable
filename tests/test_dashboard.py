"""Dashboards mensuel et annuel."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.main import app


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
        username=f"dash_{suffix}", email=None,
        password_hash=hash_password("dash12345"),
        full_name=f"Dash {suffix}", role="ADMIN", is_active=True,
    ))
    await session_owner.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/login",
                          json={"username": f"dash_{suffix}", "password": "dash12345"})
        return r.json()["access_token"]


async def _mois_id(client, headers, code):
    r = await client.get("/api/v1/mois-scolaires", headers=headers)
    return next(m for m in r.json() if m["code"] == code)["id"]


@pytest.mark.asyncio
async def test_dashboard_mensuel_vide(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    m_oct = await _mois_id(client, headers, "2026-10")
    r = await client.get(f"/api/v1/dashboard/mensuel?mois_id={m_oct}",
                         headers=headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["mois_code"] == "2026-10"
    assert d["ca_total_brut"] >= 0
    assert d["tresorerie_debut"] is not None
    assert d["tresorerie_fin"] is not None
    assert "compteurs" in d
    assert "salaires" in d


@pytest.mark.asyncio
async def test_dashboard_mensuel_avec_donnees(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]

    # Famille + élève + inscription
    r = await client.post("/api/v1/familles",
                          json={"nom": f"DashFam {suffix}"}, headers=headers)
    famille_id = r.json()["id"]
    r2 = await client.post("/api/v1/eleves",
                           json={"nom": f"E{suffix}", "prenoms": "T",
                                 "famille_id": famille_id}, headers=headers)
    eleve_id = r2.json()["id"]
    r3 = await client.get("/api/v1/niveaux", headers=headers)
    ps = next(n for n in r3.json() if n["code"] == "PS")
    m_sept = await _mois_id(client, headers, "2026-09")
    m_oct = await _mois_id(client, headers, "2026-10")
    r4 = await client.post("/api/v1/inscriptions",
                           json={"eleve_id": eleve_id, "niveau_id": ps["id"],
                                 "mois_entree_id": m_sept}, headers=headers)
    ins_id = r4.json()["id"]

    # Paiement écolage octobre
    r5 = await client.get("/api/v1/types-paiement", headers=headers)
    t_eco = next(t for t in r5.json() if t["code"] == "ECOLAGE")["id"]
    await client.post("/api/v1/paiements", json={
        "inscription_id": ins_id, "type_paiement_id": t_eco,
        "mois_concerne_id": m_oct, "montant": 100_000,
        "date_paiement": "2026-10-05",
    }, headers=headers)

    # Charge octobre
    await client.post("/api/v1/charges", json={
        "mois_id": m_oct, "libelle": "Test", "categorie": "VARIABLE",
        "montant": 20_000, "date_operation": "2026-10-12",
    }, headers=headers)

    r6 = await client.get(f"/api/v1/dashboard/mensuel?mois_id={m_oct}",
                          headers=headers)
    assert r6.status_code == 200
    d = r6.json()
    assert d["ca_total_brut"] >= 100_000
    assert d["ecolage_attendu"] >= 100_000
    assert d["ecolage_recu"] >= 100_000
    assert d["charges"] >= 20_000


@pytest.mark.asyncio
async def test_dashboard_annuel(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = await client.get("/api/v1/dashboard/annuel", headers=headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "effectif" in d
    assert len(d["mois"]) == 10
    assert "tresorerie_actuelle" in d
    assert "somme_manquante_cumulee" in d