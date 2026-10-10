"""Tests d'authentification : login, refresh, logout, RBAC."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.main import app
from app.models.user import User


@pytest_asyncio.fixture
async def client(session_owner):
    # Un nom d'utilisateur unique par exécution pytest : évite toute
    # pollution d'un run précédent (lockout, password changé, etc.).
    suffix = uuid.uuid4().hex[:8]
    username = f"testuser_{suffix}"
    password = "test1234"

    from app.models.user import User as U
    session_owner.add(U(
        username=username,
        email=None,
        password_hash=hash_password(password),
        full_name="Test User",
        role="ADMIN",
        is_active=True,
    ))
    await session_owner.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        ac._auth_username = username   # type: ignore[attr-defined]
        ac._auth_password = password   # type: ignore[attr-defined]
        yield ac


def _creds(client) -> dict[str, str]:
    return {"username": client._auth_username, "password": client._auth_password}


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["db"] is True


@pytest.mark.asyncio
async def test_login_ok(client):
    r = await client.post("/api/v1/auth/login", json=_creds(client))
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == client._auth_username


@pytest.mark.asyncio
async def test_login_mauvais_mdp(client):
    # Username aléatoire : ne touche pas au compteur de verrouillage de notre
    # utilisateur de test.
    r = await client.post(
        "/api/v1/auth/login",
        json={"username": f"ghost_{uuid.uuid4().hex[:8]}", "password": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_avec_token(client):
    r = await client.post("/api/v1/auth/login", json=_creds(client))
    token = r.json()["access_token"]
    r2 = await client.get("/api/v1/auth/me",
                          headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["username"] == client._auth_username


@pytest.mark.asyncio
async def test_me_sans_token(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_ok(client):
    r = await client.post("/api/v1/auth/login", json=_creds(client))
    refresh = r.json()["refresh_token"]
    r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


@pytest.mark.asyncio
async def test_refresh_rejoue_refuse(client):
    r = await client.post("/api/v1/auth/login", json=_creds(client))
    refresh = r.json()["refresh_token"]
    r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    r3 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r3.status_code == 401


@pytest.mark.asyncio
async def test_list_users_requires_admin(client, session_owner):
    suffix = uuid.uuid4().hex[:8]
    from app.models.user import User as U
    session_owner.add(U(
        username=f"lecteur_{suffix}", email=None,
        password_hash=hash_password("lecteur1234"),
        full_name="Lecteur", role="LECTURE", is_active=True,
    ))
    await session_owner.commit()

    r = await client.post(
        "/api/v1/auth/login",
        json={"username": f"lecteur_{suffix}", "password": "lecteur1234"},
    )
    token = r.json()["access_token"]
    r2 = await client.get("/api/v1/users",
                          headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_create_user_admin(client):
    r = await client.post("/api/v1/auth/login", json=_creds(client))
    token = r.json()["access_token"]
    payload = {
        "username": f"nouveau_comptable_{uuid.uuid4().hex[:6]}",
        "password": "comptable1234",
        "full_name": "Comptable Test",
        "role": "COMPTABLE",
    }
    r2 = await client.post("/api/v1/users", json=payload,
                           headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 201


@pytest.mark.asyncio
async def test_refresh_retourne_nouveau_refresh(client):
    r = await client.post("/api/v1/auth/login", json=_creds(client))
    old_refresh = r.json()["refresh_token"]

    r2 = await client.post("/api/v1/auth/refresh",
                           json={"refresh_token": old_refresh})
    assert r2.status_code == 200
    data = r2.json()
    assert "refresh_token" in data
    assert data["refresh_token"] != old_refresh
    assert "user" in data