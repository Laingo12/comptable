"""Référentiels et paramètres : lecture + écriture + audit."""

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
    username = f"ref_{suffix}"
    from app.models.user import User as U
    session_owner.add(U(
        username=username, email=None,
        password_hash=hash_password("ref12345"),
        full_name=f"Ref {suffix}", role="ADMIN", is_active=True,
    ))
    await session_owner.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/login",
                          json={"username": username, "password": "ref12345"})
        return r.json()["access_token"]


@pytest.mark.asyncio
async def test_list_niveaux(client, admin_token):
    r = await client.get("/api/v1/niveaux",
                         headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 10
    codes = {n["code"] for n in data}
    assert "CRECHE" in codes and "CM2" in codes


@pytest.mark.asyncio
async def test_list_mois_scolaires_active(client, admin_token):
    r = await client.get("/api/v1/mois-scolaires",
                         headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    # 10 mois scolaires + NON_DATE + HORS_ANNEE
    assert len(data) == 12
    codes = {m["code"] for m in data}
    assert "2026-09" in codes and "NON_DATE" in codes and "HORS_ANNEE" in codes


@pytest.mark.asyncio
async def test_list_types_modes(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r1 = await client.get("/api/v1/types-paiement", headers=headers)
    r2 = await client.get("/api/v1/modes-paiement", headers=headers)
    assert r1.status_code == 200 and len(r1.json()) == 4
    assert r2.status_code == 200 and len(r2.json()) == 5


@pytest.mark.asyncio
async def test_upsert_parametre_and_audit(client, admin_token, session_app):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = await client.get("/api/v1/annees/active", headers=headers)
    annee_id = r.json()["id"]
    url = f"/api/v1/parametres?annee_scolaire_id={annee_id}"

    # 1) Force une valeur connue : 1
    r1 = await client.put(
        url,
        json={"cle": "jour_limite_paiement", "valeur": 1, "description": "Test"},
        headers=headers,
    )
    assert r1.status_code == 200
    assert r1.json()["valeur"] == 1
    param_id = r1.json()["id"]

    # 2) Transition garantie : 1 → 7
    r2 = await client.put(
        url,
        json={"cle": "jour_limite_paiement", "valeur": 7, "description": "Test"},
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json()["valeur"] == 7

    # 3) La dernière ligne d'audit UPDATE doit contenir le diff 1 → 7
    row = (await session_app.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "parametres",
            AuditLog.entity_id == str(param_id),
            AuditLog.action == "UPDATE",
        ).order_by(AuditLog.id.desc()).limit(1)
    )).scalar_one()

    assert row.after_state is not None
    assert row.after_state.get("valeur") == 7
    assert row.before_state is not None
    assert row.before_state.get("valeur") == 1
    # Aucun secret ni hash dans le diff
    blob = f"{row.before_state} {row.after_state}".lower()
    assert "password" not in blob
    assert "$argon2" not in blob

    # 4) Remise de la valeur initiale
    await client.put(
        url,
        json={"cle": "jour_limite_paiement", "valeur": 5},
        headers=headers,
    )


@pytest.mark.asyncio
async def test_upsert_parametre_type_invalide(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = await client.put(
        "/api/v1/parametres",
        json={"cle": "jour_limite_paiement", "valeur": "cinq"},
        headers=headers,
    )
    assert r.status_code == 400
    assert "entier" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upsert_grille_and_audit(client, admin_token, session_app):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = await client.get("/api/v1/annees/active", headers=headers)
    annee_id = r.json()["id"]
    # Niveau PS
    r2 = await client.get("/api/v1/niveaux", headers=headers)
    ps = next(n for n in r2.json() if n["code"] == "PS")

    payload = {"niveau_id": ps["id"], "ecolage_mensuel": 125_000,
               "droit_inscription": 55_000, "frais_generaux": 10_000}
    r3 = await client.put(
        f"/api/v1/grille-tarifaire/{annee_id}/{ps['id']}",
        json=payload, headers=headers,
    )
    assert r3.status_code == 200
    assert r3.json()["ecolage_mensuel"] == 125_000
    grille_id = r3.json()["id"]

    rows = (await session_app.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "grille_tarifaire",
            AuditLog.entity_id == str(grille_id),
        ).order_by(AuditLog.id.desc()).limit(1)
    )).scalars().all()
    assert rows, "Audit grille manquant"


@pytest.mark.asyncio
async def test_lecture_cannot_write_parametres(client, session_owner, session_app):
    """Un LECTURE peut lire les référentiels mais pas écrire les paramètres."""
    suffix = uuid.uuid4().hex[:8]
    username = f"lec_{suffix}"
    from app.models.user import User as U
    session_owner.add(U(
        username=username, email=None,
        password_hash=hash_password("lec12345"),
        full_name=f"Lec {suffix}", role="LECTURE", is_active=True,
    ))
    await session_owner.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/login",
                          json={"username": username, "password": "lec12345"})
        token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Lecture OK
    r1 = await client.get("/api/v1/niveaux", headers=headers)
    assert r1.status_code == 200
    # Écriture refusée
    r2 = await client.put(
        "/api/v1/parametres",
        json={"cle": "devise", "valeur": "USD"},
        headers=headers,
    )
    assert r2.status_code == 403