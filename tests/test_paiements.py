"""Paiements : création, annulation, audit, RBAC."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.main import app
from app.models.audit import AuditLog
from app.models.paiements import Paiement


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


async def _login(client, username, password):
    return await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )


@pytest_asyncio.fixture
async def admin_ctx(session_owner):
    suffix = uuid.uuid4().hex[:8]
    username = f"pay_{suffix}"
    from app.models.user import User as U
    session_owner.add(U(
        username=username, email=None,
        password_hash=hash_password("pay12345"),
        full_name=f"Pay {suffix}", role="ADMIN", is_active=True,
    ))
    await session_owner.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await _login(ac, username, "pay12345")
        return r.json()["access_token"], username, suffix


async def _setup_inscription(client, headers, suffix: str) -> tuple[int, int, int]:
    """Crée famille + élève + inscription, retourne (inscription_id, niveau_id, eleve_id)."""
    r = await client.post("/api/v1/familles",
                          json={"nom": f"PayFam {suffix}"}, headers=headers)
    famille_id = r.json()["id"]

    r2 = await client.post("/api/v1/eleves",
                           json={"nom": "Payeur", "prenoms": suffix,
                                 "famille_id": famille_id}, headers=headers)
    eleve_id = r2.json()["id"]

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
    return r5.json()["id"], ps["id"], eleve_id


async def _type_eco(client, headers) -> int:
    r = await client.get("/api/v1/types-paiement", headers=headers)
    return next(t for t in r.json() if t["code"] == "ECOLAGE")["id"]


async def _mois_oct(client, headers) -> int:
    r = await client.get("/api/v1/mois-scolaires", headers=headers)
    return next(m for m in r.json() if m["code"] == "2026-10")["id"]


@pytest.mark.asyncio
async def test_create_paiement_ecolage_and_audit(client, admin_ctx, session_app):
    token, _, suffix = admin_ctx
    headers = {"Authorization": f"Bearer {token}"}

    inscription_id, _, _ = await _setup_inscription(client, headers, suffix)
    t_eco = await _type_eco(client, headers)
    m_oct = await _mois_oct(client, headers)

    r = await client.post(
        "/api/v1/paiements",
        json={
            "inscription_id": inscription_id,
            "type_paiement_id": t_eco,
            "mois_concerne_id": m_oct,
            "montant": 100_000,
            "date_paiement": "2026-10-08",
            "reference": "REC-001",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    p = r.json()
    assert p["montant"] == 100_000
    assert p["mois_concerne_id"] == m_oct

    # Audit INSERT
    row = (await session_app.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "paiements",
            AuditLog.entity_id == str(p["id"]),
            AuditLog.action == "INSERT",
        ).limit(1)
    )).scalar_one_or_none()
    assert row is not None
    assert row.after_state.get("montant") == 100_000


@pytest.mark.asyncio
async def test_create_ecolage_sans_mois_refuse(client, admin_ctx):
    token, _, suffix = admin_ctx
    headers = {"Authorization": f"Bearer {token}"}
    inscription_id, _, _ = await _setup_inscription(client, headers, suffix)
    t_eco = await _type_eco(client, headers)

    r = await client.post(
        "/api/v1/paiements",
        json={"inscription_id": inscription_id, "type_paiement_id": t_eco,
              "montant": 50_000, "date_paiement": "2026-10-05"},
        headers=headers,
    )
    assert r.status_code == 400
    assert "mois_concerne_id" in r.json()["detail"]


@pytest.mark.asyncio
async def test_annulation_ecriture_inverse(client, admin_ctx, session_app):
    token, _, suffix = admin_ctx
    headers = {"Authorization": f"Bearer {token}"}
    inscription_id, _, _ = await _setup_inscription(client, headers, suffix)
    t_eco = await _type_eco(client, headers)
    m_oct = await _mois_oct(client, headers)

    r = await client.post(
        "/api/v1/paiements",
        json={"inscription_id": inscription_id, "type_paiement_id": t_eco,
              "mois_concerne_id": m_oct, "montant": 75_000,
              "date_paiement": "2026-10-08"},
        headers=headers,
    )
    pid = r.json()["id"]

    r2 = await client.post(
        f"/api/v1/paiements/{pid}/annuler",
        json={"motif": "Erreur de saisie"},
        headers=headers,
    )
    assert r2.status_code == 201, r2.text
    inv = r2.json()
    assert inv["montant"] == -75_000
    assert inv["parent_paiement_id"] == pid
    assert inv["motif_annulation"] == "Erreur de saisie"

    # Double annulation refusée
    r3 = await client.post(
        f"/api/v1/paiements/{pid}/annuler",
        json={"motif": "Encore"},
        headers=headers,
    )
    assert r3.status_code == 400

    # L'original reste immuable
    original = (await session_app.execute(
        select(Paiement).where(Paiement.id == pid)
    )).scalar_one()
    assert original.montant == 75_000  # inchangé


@pytest.mark.asyncio
async def test_list_filtre_par_type_et_annules(client, admin_ctx):
    token, _, suffix = admin_ctx
    headers = {"Authorization": f"Bearer {token}"}
    inscription_id, _, _ = await _setup_inscription(client, headers, suffix)
    t_eco = await _type_eco(client, headers)
    m_oct = await _mois_oct(client, headers)

    r = await client.post(
        "/api/v1/paiements",
        json={"inscription_id": inscription_id, "type_paiement_id": t_eco,
              "mois_concerne_id": m_oct, "montant": 10_000,
              "date_paiement": "2026-10-05"},
        headers=headers,
    )
    pid = r.json()["id"]

    r2 = await client.post(f"/api/v1/paiements/{pid}/annuler",
                           json={"motif": "test"}, headers=headers)
    assert r2.status_code == 201
    inverse_id = r2.json()["id"]

    # Par défaut : seuls les paiements non annulés
    r3 = await client.get(
        f"/api/v1/paiements?inscription_id={inscription_id}",
        headers=headers,
    )
    ids = [x["id"] for x in r3.json()["items"]]
    assert pid in ids
    assert inverse_id not in ids

    # include_annules=true : les deux
    r4 = await client.get(
        f"/api/v1/paiements?inscription_id={inscription_id}&include_annules=true",
        headers=headers,
    )
    ids2 = [x["id"] for x in r4.json()["items"]]
    assert pid in ids2
    assert inverse_id in ids2


@pytest.mark.asyncio
async def test_saisie_ne_peut_pas_annuler(client, session_owner):
    """Le rôle SAISIE peut créer mais pas annuler."""
    suffix = uuid.uuid4().hex[:8]
    from app.models.user import User as U
    session_owner.add(U(
        username=f"sai_{suffix}", email=None,
        password_hash=hash_password("sai12345"),
        full_name=f"Sai {suffix}", role="SAISIE", is_active=True,
    ))
    await session_owner.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await _login(ac, f"sai_{suffix}", "sai12345")
        token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # La création est autorisée par RBAC ; on ne teste ici que le refus d'annulation.
    r2 = await client.post(
        "/api/v1/paiements/1/annuler",
        json={"motif": "test"},
        headers=headers,
    )
    # 403 car SAISIE n'a pas ANNULER
    assert r2.status_code == 403