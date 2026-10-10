"""Endpoints d'authentification."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.schemas.auth import (
    AccessToken,
    ChangePasswordRequest,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    TokenPair,
)
from app.schemas.user import UserRead
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login_endpoint(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    try:
        user, access, refresh_token = await auth_service.login(
            session, body.username, body.password,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except auth_service.AuthError:
        # On persiste la ligne d'audit LOGIN ko avant de propager le 401.
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
        )
    return TokenPair(
        access_token=access,
        refresh_token=refresh_token,
        user=UserRead.model_validate(user),
    )


@router.post("/refresh", response_model=AccessToken)
async def refresh_endpoint(
    body: RefreshRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AccessToken:
    try:
        user, access, _new_refresh = await auth_service.refresh(
            session, body.refresh_token,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except auth_service.AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    return AccessToken(
        access_token=access,
        user=UserRead.model_validate(user),
    )


@router.post("/logout")
async def logout_endpoint(
    body: RefreshRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    await auth_service.logout(session, body.refresh_token, user)
    return {"ok": True}


@router.post("/logout-all")
async def logout_all_endpoint(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    await auth_service.logout_all(session, user)
    return {"ok": True}


@router.post("/change-password")
async def change_password_endpoint(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    try:
        await auth_service.change_password(
            session, user, body.current_password, body.new_password
        )
    except auth_service.AuthError as exc:
        # Audit de la tentative avant propagation.
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me_endpoint(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse.model_validate(user)