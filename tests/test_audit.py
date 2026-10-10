"""Écriture d'audit : LOGIN ok/ko, INSERT, UPDATE, absence de secrets."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from app.core.security import hash_password
from app.main import app
from app.models.audit import AuditLog
from app.models.user import User


@pytest.mark.asyncio
async def test_audit_login_ok_and_ko(session_owner, session_app):
    from app.models.user import User as U
    existing = await session_owner.scalar(select(U).where(U.username == "aud1"))
    if existing is None:
        session_owner.add(U(
            username="aud1", email=None,
            password_hash=hash_password("aud12345"),
            full_name="Aud 1", role="ADMIN", is_active=True,
        ))
        await session_owner.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/api/v1/auth/login",
                      json={"username": "aud1", "password": "aud12345"})
        await ac.post("/api/v1/auth/login",
                      json={"username": "aud1", "password": "wrong"})

    rows = (await session_app.execute(
        select(AuditLog).where(AuditLog.action == "LOGIN")
    )).scalars().all()
    oks = [r for r in rows if r.after_state and r.after_state.get("ok") is True]
    kos = [r for r in rows if r.after_state and r.after_state.get("ok") is False]
    assert oks and kos


@pytest.mark.asyncio
async def test_audit_insert_and_update_user(session_owner, session_app):
    from app.models.user import User as U
    existing = await session_owner.scalar(select(U).where(U.username == "aud2"))
    if existing is not None:
        await session_owner.execute(text("DELETE FROM users WHERE username = 'aud2'"))
        await session_owner.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/login",
                          json={"username": "aud1", "password": "aud12345"})
        token = r.json()["access_token"]
        r2 = await ac.post(
            "/api/v1/users",
            json={"username": "aud2", "password": "aud12345",
                  "full_name": "Aud 2", "role": "LECTURE"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 201
        uid = r2.json()["id"]
        r3 = await ac.patch(
            f"/api/v1/users/{uid}",
            json={"full_name": "Aud 2 renamed"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r3.status_code == 200

    rows = (await session_app.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "users", AuditLog.entity_id == str(uid)
        ).order_by(AuditLog.id)
    )).scalars().all()
    actions = [r.action for r in rows]
    assert "INSERT" in actions and "UPDATE" in actions

    for r in rows:
        blob = f"{r.before_state} {r.after_state}".lower()
        assert "password_hash" not in blob
        assert "$argon2" not in blob