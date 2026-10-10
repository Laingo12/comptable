"""Service d'authentification : login, refresh, logout, change-password."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.models.user import User
from app.repositories.users import UserRepository


class AuthError(Exception):
    """Erreur d'authentification (message générique côté API)."""


async def _audit(
    session: AsyncSession,
    user_id: int | None,
    action: str,
    ip: str | None,
    user_agent: str | None,
    entity_id: str | None = None,
    detail: dict | None = None,
) -> None:
    session.add(AuditLog(
        user_id=user_id,
        action=action,
        entity_type="auth",
        entity_id=entity_id,
        before_state=None,
        after_state=detail,
        ip=ip,
        user_agent=user_agent,
    ))
    await session.flush()


async def _failed_login_count(session: AsyncSession, username: str) -> int:
    settings = get_settings()
    since = datetime.now(timezone.utc) - timedelta(minutes=settings.login_lockout_minutes)
    stmt = select(func.count(AuditLog.id)).where(
        AuditLog.action == AuditAction.LOGIN.value,
        AuditLog.entity_id == username,
        AuditLog.after_state["ok"].astext == "false",
        AuditLog.created_at >= since,
    )
    return (await session.execute(stmt)).scalar_one() or 0


async def login(
    session: AsyncSession, username: str, password: str,
    ip: str | None, user_agent: str | None,
) -> tuple[User, str, str]:
    settings = get_settings()

    if await _failed_login_count(session, username) >= settings.login_max_attempts:
        await _audit(
            session, None, AuditAction.LOGIN.value, ip, user_agent,
            entity_id=username, detail={"ok": False, "reason": "locked"},
        )
        raise AuthError("Compte temporairement verrouillé")

    repo = UserRepository(session)
    user = await repo.by_username(username)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        await _audit(
            session,
            user.id if user else None,
            AuditAction.LOGIN.value,
            ip, user_agent,
            entity_id=username,
            detail={"ok": False},
        )
        raise AuthError("Identifiants invalides")

    access = create_access_token(user.id, user.role)
    refresh_token, refresh_hash, expires_at = create_refresh_token(user.id)
    await repo.store_refresh_token(user.id, refresh_hash, expires_at, user_agent, ip)

    user.last_login_at = datetime.now(timezone.utc)
    await _audit(
        session, user.id, AuditAction.LOGIN.value, ip, user_agent,
        entity_id=str(user.id), detail={"ok": True},
    )
    return user, access, refresh_token


async def refresh(
    session: AsyncSession, refresh_token: str,
    ip: str | None, user_agent: str | None,
) -> tuple[User, str, str]:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise AuthError("Refresh token invalide") from exc

    if payload.get("typ") != "refresh":
        raise AuthError("Type de token invalide")

    user_id = int(payload["sub"])
    token_hash = hash_refresh_token(refresh_token)

    repo = UserRepository(session)
    stored = await repo.find_refresh_token(token_hash)
    if stored is None:
        raise AuthError("Refresh token inconnu")
    if stored.revoked_at is not None:
        # Réutilisation d'un token déjà révoqué → révocation de toute la famille
        await repo.revoke_family(stored.family_id)
        raise AuthError("Refresh token révoqué")
    if stored.expires_at <= datetime.now(timezone.utc):
        raise AuthError("Refresh token expiré")

    user = await repo.by_id(user_id)
    if user is None or not user.is_active:
        raise AuthError("Utilisateur invalide")

    await repo.revoke_refresh_token(stored)

    access = create_access_token(user.id, user.role)
    new_token, new_hash, new_expires = create_refresh_token(user.id)
    await repo.store_refresh_token(
        user.id, new_hash, new_expires, user_agent, ip,
        family_id=stored.family_id,
    )
    return user, access, new_token


async def logout(
    session: AsyncSession, refresh_token: str, user: User,
) -> None:
    repo = UserRepository(session)
    token_hash = hash_refresh_token(refresh_token)
    stored = await repo.find_refresh_token(token_hash)
    if stored is not None and stored.revoked_at is None:
        await repo.revoke_refresh_token(stored)
    await _audit(
        session, user.id, AuditAction.LOGOUT.value, None, None,
        entity_id=str(user.id), detail=None,
    )


async def logout_all(session: AsyncSession, user: User) -> None:
    repo = UserRepository(session)
    await repo.revoke_all_refresh_tokens(user.id)
    await _audit(
        session, user.id, AuditAction.LOGOUT.value, None, None,
        entity_id=str(user.id), detail={"all": True},
    )


async def change_password(
    session: AsyncSession, user: User,
    current_password: str, new_password: str,
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AuthError("Mot de passe actuel incorrect")
    user.password_hash = hash_password(new_password)
    await UserRepository(session).revoke_all_refresh_tokens(user.id)
    await _audit(
        session, user.id, AuditAction.UPDATE.value, None, None,
        entity_id=str(user.id), detail={"action": "change_password"},
    )