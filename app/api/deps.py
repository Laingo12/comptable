"""Dépendances FastAPI : session, utilisateur courant, contrôle d'accès."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.user import User
from app.permissions.rbac import Action, Resource, has_permission
from app.repositories.users import UserRepository

_bearer = HTTPBearer(auto_error=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Fournit une session par requête, avec contexte d'audit initial."""
    async with SessionLocal() as session:
        session.info["audit_context"] = {
            "user_id": None,
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("typ") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Type de token invalide",
        )

    user = await UserRepository(session).by_id(int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur invalide ou désactivé",
        )

    request.state.user_id = user.id
    session.info["audit_context"]["user_id"] = user.id
    return user


def require_permission(resource: Resource, action: Action):
    """Retourne une dépendance qui vérifie (resource, action) pour le rôle courant."""
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user.role, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle {user.role} non autorisé pour {resource.value}:{action.value}",
            )
        return user
    return _checker


def require_role(*roles: str):
    """Variante pour les cas simples (ex : admin uniquement)."""
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle requis : {', '.join(roles)}",
            )
        return user
    return _checker