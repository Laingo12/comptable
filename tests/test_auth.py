"""Tests d'authentification : login, refresh, logout, RBAC."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.main import app
from app.models.user import User


@pytest_asyncio.fixture
async def client(session_owner):
    # On prépare un user de test en base via la fixture owner (droits DML)
    from app.models.user import User as U
    existing = await session_owner.scalar(select(U).where(U.username == "testuser"))
    if existing is None:
        session_owner.add(U(
            username="testuser",
            email=None,
            password_hash=hash_password("test1234"),
            full_name="Test User",
            role="ADMIN",
            is_active=True,
        ))
        await session_owner.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["db"] is True


@pytest.mark.asyncio
async def test_login_ok(client):
    r = await client.post("/api/v1/auth/login",
                          json={"username": "testuser", "password": "test1234"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_login_mauvais_mdp(client):
    r = await client.post("/api/v1/auth/login",
                          json={"username": "testuser", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_avec_token(client):
    r = await client.post("/api/v1/auth/login",
                          json={"username": "testuser", "password": "test1234"})
    token = r.json()["access_token"]
    r2 = await client.get("/api/v1/auth/me",
                          headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["username"] == "testuser"


@pytest.mark.asyncio
async def test_me_sans_token(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_ok(client):
    r = await client.post("/api/v1/auth/login",
                          json={"username": "testuser", "password": "test1234"})
    refresh = r.json()["refresh_token"]
    r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


@pytest.mark.asyncio
async def test_refresh_rejoue_refuse(client):
    r = await client.post("/api/v1/auth/login",
                          json={"username": "testuser", "password": "test1234"})
    refresh = r.json()["refresh_token"]
    r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    r3 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r3.status_code == 401


@pytest.mark.asyncio
async def test_list_users_requires_admin(client, session_owner):
    from app.models.user import User as U
    existing = await session_owner.scalar(select(U).where(U.username == "lecteur"))
    if existing is None:
        session_owner.add(U(
            username="lecteur", email=None,
            password_hash=hash_password("lecteur1234"),
            full_name="Lecteur", role="LECTURE", is_active=True,
        ))
        await session_owner.commit()

    r = await client.post("/api/v1/auth/login",
                          json={"username": "lecteur", "password": "lecteur1234"})
    token = r.json()["access_token"]
    r2 = await client.get("/api/v1/users",
                          headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_create_user_admin(client):
    r = await client.post("/api/v1/auth/login",
                          json={"username": "testuser", "password": "test1234"})
    token = r.json()["access_token"]
    payload = {
        "username": "nouveau_comptable",
        "password": "comptable1234",
        "full_name": "Comptable Test",
        "role": "COMPTABLE",
    }
    r2 = await client.post("/api/v1/users", json=payload,
                           headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code in (201, 409)