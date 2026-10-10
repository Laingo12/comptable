"""Situation écolage : fiche élève, avances, retards, statuts."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

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
        username=f"sit_{suffix}", email=None,
        password_hash=hash_password("sit12345"),
        full_name=f"Sit {suffix}", role="ADMIN", is_active=True,
    ))
    await session_owner.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/login",
                          json={"username": f"sit_{suffix}", "password": "sit12345"})
        return r.json()["access_token"]


async def _setup(client, headers, suffix):
    """Famille + élève + inscription. Retourne (eleve_id, inscription_id, t_eco, mois_ids)."""
    r = await client.post("/api/v1/familles",
                          json={"nom": f"SitFam {suffix}"}, headers=headers)
    famille_id = r.json()["id"]

    r2 = await client.post("/api/v1/eleves",
                           json={"nom": "Sit", "prenoms": suffix,
                                 "famille_id": famille_id}, headers=headers)
    eleve_id = r2.json()["id"]

    r3 = await client.get("/api/v1/niveaux", headers=headers)
    ps = next(n for n in r3.json() if n["code"] == "PS")
    r4 = await client.get("/api/v1/mois-scolaires", headers=headers)
    mois = {m["code"]: m for m in r4.json()}
    m09 = mois["2026-09"]

    r5 = await client.post(
        "/api/v1/inscriptions",
        json={"eleve_id": eleve_id, "niveau_id": ps["id"], "mois_entree_id": m09["id"]},
        headers=headers,
    )
    assert r5.status_code == 201, r5.text
    inscription_id = r5.json()["id"]

    r6 = await client.get("/api/v1/types-paiement", headers=headers)
    t_eco = next(t for t in r6.json() if t["code"] == "ECOLAGE")["id"]
    return eleve_id, inscription_id, t_eco, mois


@pytest.mark.asyncio
async def test_situation_vide(client, admin_token):
    token = admin_token
    headers = {"Authorization": f"Bearer {token}"}
    suffix = uuid.uuid4().hex[:6]
    eleve_id, inscription_id, _, _ = await _setup(client, headers, suffix)

    r = await client.get(f"/api/v1/eleves/{eleve_id}/situation", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    # 10 mois scolaires (Sept → Juin)
    assert len(data["mois"]) == 10
    assert data["totaux"]["paye"] == 0
    assert data["totaux"]["reste_du"] > 0
    assert data["totaux"]["taux_recouvrement"] == 0.0
    for m in data["mois"]:
        assert m["statut"] == "IMPAYE"
        assert m["paye"] == 0


@pytest.mark.asyncio
async def test_situation_paiement_partiel_puis_complet(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]
    eleve_id, inscription_id, t_eco, mois = await _setup(client, headers, suffix)
    m_sept = mois["2026-09"]

    # 1) Paiement partiel
    r = await client.post("/api/v1/paiements", json={
        "inscription_id": inscription_id, "type_paiement_id": t_eco,
        "mois_concerne_id": m_sept["id"], "montant": 30_000,
        "date_paiement": "2026-09-04",
    }, headers=headers)
    assert r.status_code == 201

    r2 = await client.get(f"/api/v1/eleves/{eleve_id}/situation", headers=headers)
    sept = next(m for m in r2.json()["mois"] if m["code"] == "2026-09")
    assert sept["statut"] == "PARTIEL"
    assert sept["paye"] == 30_000
    assert sept["reste_du"] > 0

    # 2) Complète
    du = sept["du"]
    r3 = await client.post("/api/v1/paiements", json={
        "inscription_id": inscription_id, "type_paiement_id": t_eco,
        "mois_concerne_id": m_sept["id"], "montant": du - 30_000,
        "date_paiement": "2026-09-05",
    }, headers=headers)
    assert r3.status_code == 201

    r4 = await client.get(f"/api/v1/eleves/{eleve_id}/situation", headers=headers)
    sept2 = next(m for m in r4.json()["mois"] if m["code"] == "2026-09")
    assert sept2["statut"] == "PAYE"
    assert sept2["reste_du"] == 0
    assert len(sept2["paiements"]) == 2


@pytest.mark.asyncio
async def test_qualificatif_avance_et_retard(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]
    eleve_id, inscription_id, t_eco, mois = await _setup(client, headers, suffix)

    m_sept = mois["2026-09"]
    m_oct = mois["2026-10"]

    # Avance : on paie en septembre pour octobre
    await client.post("/api/v1/paiements", json={
        "inscription_id": inscription_id, "type_paiement_id": t_eco,
        "mois_concerne_id": m_oct["id"], "montant": 100_000,
        "date_paiement": "2026-09-20",
    }, headers=headers)

    # Retard : on paie en octobre pour septembre
    await client.post("/api/v1/paiements", json={
        "inscription_id": inscription_id, "type_paiement_id": t_eco,
        "mois_concerne_id": m_sept["id"], "montant": 100_000,
        "date_paiement": "2026-10-15",
    }, headers=headers)

    r = await client.get(f"/api/v1/eleves/{eleve_id}/situation", headers=headers)
    data = r.json()
    sept = next(m for m in data["mois"] if m["code"] == "2026-09")
    oct = next(m for m in data["mois"] if m["code"] == "2026-10")

    # Le paiement de septembre concerne septembre mais a été payé en octobre → RETARD
    assert sept["paiements"][0]["qualificatif"] == "RETARD"
    # Le paiement pour octobre a été payé en septembre → AVANCE
    assert oct["paiements"][0]["qualificatif"] == "AVANCE"


@pytest.mark.asyncio
async def test_droits_inscription_dans_totaux(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]
    eleve_id, inscription_id, _, _ = await _setup(client, headers, suffix)

    # Récupère le type INSCRIPTION
    r0 = await client.get("/api/v1/types-paiement", headers=headers)
    t_insc = next(t for t in r0.json() if t["code"] == "INSCRIPTION")["id"]

    # Paie les droits
    r1 = await client.get(f"/api/v1/eleves/{eleve_id}/situation", headers=headers)
    droits_du = r1.json()["droits_inscription"]["du"]
    if droits_du > 0:
        r2 = await client.post("/api/v1/paiements", json={
            "inscription_id": inscription_id, "type_paiement_id": t_insc,
            "montant": droits_du, "date_paiement": "2026-09-01",
        }, headers=headers)
        assert r2.status_code == 201

    r3 = await client.get(f"/api/v1/eleves/{eleve_id}/situation", headers=headers)
    data = r3.json()
    assert data["droits_inscription"]["statut"] == "PAYE"
    assert data["droits_inscription"]["reste_du"] == 0
    # Le total inclut bien les droits
    assert data["totaux"]["paye"] >= droits_du