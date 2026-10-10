"""Verrouillage, change-password, famille de refresh, dernier ADMIN."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.config import get_settings
from app.core.security import hash_password
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def fresh_admin(session_owner):
    """Un ADMIN unique par test, isolé par un suffixe UUID."""
    suffix = uuid.uuid4().hex[:8]
    username = f"adv_{suffix}"
    password = "adv12345"
    from app.models.user import User as U
    session_owner.add(U(
        username=username, email=None,
        password_hash=hash_password(password),
        full_name=f"Adv {suffix}", role="ADMIN", is_active=True,
    ))
    await session_owner.commit()
    yield username, password


async def _login(client, username, password):
    return await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )


@pytest.mark.asyncio
async def test_lockout_after_n_failures(client, fresh_admin):
    username, password = fresh_admin
    s = get_settings()
    for _ in range(s.login_max_attempts):
        r = await _login(client, username, "wrong")
        assert r.status_code == 401
    # Le mot de passe correct est désormais refusé : compte verrouillé.
    r = await _login(client, username, password)
    assert r.status_code == 401
    # Pas de nettoyage : audit_log est immuable, la donnée reste.


@pytest.mark.asyncio
async def test_change_password_revokes_refresh(client, fresh_admin):
    username, password = fresh_admin
    r = await _login(client, username, password)
    assert r.status_code == 200, r.text
    tokens = r.json()
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    r2 = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": password, "new_password": "adv67890"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r2.status_code == 200

    # L'ancien refresh est révoqué
    r3 = await client.post("/api/v1/auth/refresh",
                           json={"refresh_token": refresh})
    assert r3.status_code == 401


@pytest.mark.asyncio
async def test_refresh_reuse_revokes_family(client, fresh_admin):
    username, password = fresh_admin
    r = await _login(client, username, password)
    assert r.status_code == 200, r.text
    refresh1 = r.json()["refresh_token"]

    # Rotation : refresh1 → refresh2 (refresh1 révoqué)
    r2 = await client.post("/api/v1/auth/refresh",
                           json={"refresh_token": refresh1})
    assert r2.status_code == 200

    # Réutilisation de refresh1 → 401 et révocation de toute la famille
    r3 = await client.post("/api/v1/auth/refresh",
                           json={"refresh_token": refresh1})
    assert r3.status_code == 401


@pytest.mark.asyncio
async def test_last_admin_protected(client, fresh_admin, session_owner):
    username, password = fresh_admin

    # Isole le test : désactive temporairement tous les autres ADMIN actifs.
    await session_owner.execute(
        text("UPDATE users SET is_active = false "
             "WHERE role = 'ADMIN' AND username != :u"),
        {"u": username},
    )
    await session_owner.commit()

    try:
        r = await _login(client, username, password)
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        uid = me.json()["id"]

        r2 = await client.patch(
            f"/api/v1/users/{uid}",
            json={"role": "LECTURE"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 400
        assert "dernier ADMIN" in r2.json()["detail"]
    finally:
        # Restaure l'état initial des autres ADMIN.
        await session_owner.execute(
            text("UPDATE users SET is_active = true "
                 "WHERE role = 'ADMIN' AND username != :u"),
            {"u": username},
        )
        await session_owner.commit()