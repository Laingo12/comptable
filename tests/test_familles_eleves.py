"""Familles, élèves, inscriptions : CRUD, audit, remise fratrie, RBAC."""

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
        username=f"scol_{suffix}", email=None,
        password_hash=hash_password("scol1234"),
        full_name=f"Scol {suffix}", role="ADMIN", is_active=True,
    ))
    await session_owner.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/login",
                          json={"username": f"scol_{suffix}", "password": "scol1234"})
        return r.json()["access_token"]


@pytest.mark.asyncio
async def test_create_famille_eleve_inscription_and_audit(
    client, admin_token, session_app,
):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]

    # Famille
    r = await client.post("/api/v1/familles",
                          json={"nom": f"Famille {suffix}", "telephone": f"034{suffix}"},
                          headers=headers)
    assert r.status_code == 201
    famille_id = r.json()["id"]

    # Élève avec matricule auto
    r2 = await client.post("/api/v1/eleves",
                           json={"nom": "Rakoto", "prenoms": f"Naina{suffix}",
                                 "sexe": "M", "famille_id": famille_id},
                           headers=headers)
    assert r2.status_code == 201
    eleve = r2.json()
    assert eleve["matricule"].startswith("SK-")
    eleve_id = eleve["id"]

    # Inscription (niveau PS, mois 2026-09)
    r3 = await client.get("/api/v1/niveaux", headers=headers)
    ps = next(n for n in r3.json() if n["code"] == "PS")
    r4 = await client.get("/api/v1/mois-scolaires", headers=headers)
    m09 = next(m for m in r4.json() if m["code"] == "2026-09")

    r5 = await client.post(
        "/api/v1/inscriptions",
        json={"eleve_id": eleve_id, "niveau_id": ps["id"], "mois_entree_id": m09["id"]},
        headers=headers,
    )
    assert r5.status_code == 201, r5.text
    ins = r5.json()
    assert ins["ecolage_mensuel"] > 0
    assert ins["remise_pct"] == 0  # seul enfant
    assert ins["statut"] == "ACTIF"

    # Audit : famille, eleve, inscription capturés
    for table, eid in [("familles", famille_id), ("eleves", eleve_id),
                       ("inscriptions", ins["id"])]:
        row = (await session_app.execute(
            select(AuditLog).where(
                AuditLog.entity_type == table,
                AuditLog.entity_id == str(eid),
                AuditLog.action == "INSERT",
            ).limit(1)
        )).scalar_one_or_none()
        assert row is not None, f"Audit INSERT manquant pour {table}"


@pytest.mark.asyncio
async def test_remise_fratrie_10_pct(client, admin_token, session_app):
    """Deux enfants actifs dans la même famille → remise 10 % automatique."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]

    r = await client.post("/api/v1/familles",
                          json={"nom": f"Frere {suffix}"}, headers=headers)
    famille_id = r.json()["id"]

    r2 = await client.get("/api/v1/niveaux", headers=headers)
    ps = next(n for n in r2.json() if n["code"] == "PS")
    r3 = await client.get("/api/v1/mois-scolaires", headers=headers)
    m09 = next(m for m in r3.json() if m["code"] == "2026-09")

    ids = []
    for i in range(2):
        r4 = await client.post(
            "/api/v1/eleves",
            json={"nom": f"Enfant{i}", "prenoms": suffix, "famille_id": famille_id},
            headers=headers,
        )
        eid = r4.json()["id"]
        ids.append(eid)
        r5 = await client.post(
            "/api/v1/inscriptions",
            json={"eleve_id": eid, "niveau_id": ps["id"], "mois_entree_id": m09["id"]},
            headers=headers,
        )
        assert r5.status_code == 201, r5.text

    # Après le 2e enfant : les deux inscriptions doivent avoir remise_pct = 10
    for eid in ids:
        r6 = await client.get(f"/api/v1/inscriptions?eleve_id={eid}", headers=headers)
        ins = r6.json()["items"][0]
        assert ins["remise_pct"] == 10, ins


@pytest.mark.asyncio
async def test_update_eleve_audit(client, admin_token, session_app):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]

    r = await client.post("/api/v1/eleves",
                          json={"nom": "Avant", "prenoms": suffix},
                          headers=headers)
    eid = r.json()["id"]

    r2 = await client.patch(f"/api/v1/eleves/{eid}",
                            json={"nom": "Apres"}, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["nom"] == "Apres"

    row = (await session_app.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "eleves",
            AuditLog.entity_id == str(eid),
            AuditLog.action == "UPDATE",
        ).order_by(AuditLog.id.desc()).limit(1)
    )).scalar_one_or_none()
    assert row is not None
    assert row.after_state.get("nom") == "Apres"


@pytest.mark.asyncio
async def test_list_pagination_and_search(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]
    for i in range(3):
        await client.post("/api/v1/eleves",
                          json={"nom": f"Zed{suffix}", "prenoms": f"P{i}"},
                          headers=headers)
    r = await client.get(
        f"/api/v1/eleves?q={suffix}&page=1&page_size=2&sort=nom:asc",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 3
    assert len(data["items"]) == 2
    assert data["page"] == 1 and data["page_size"] == 2


@pytest.mark.asyncio
async def test_lecture_cannot_create(client, session_owner):
    suffix = uuid.uuid4().hex[:8]
    from app.models.user import User as U
    session_owner.add(U(
        username=f"ro_{suffix}", email=None,
        password_hash=hash_password("ro123456"),
        full_name=f"RO {suffix}", role="LECTURE", is_active=True,
    ))
    await session_owner.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/login",
                          json={"username": f"ro_{suffix}", "password": "ro123456"})
        token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r1 = await client.get("/api/v1/eleves", headers=headers)
    assert r1.status_code == 200
    r2 = await client.post("/api/v1/eleves",
                           json={"nom": "X", "prenoms": "Y"},
                           headers=headers)
    assert r2.status_code == 403