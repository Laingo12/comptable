"""Endpoints utilisateurs — ADMIN uniquement."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.core.security import hash_password
from app.models.enums import Role
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.users import UserRepository
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
async def list_users(
    _: User = Depends(require_permission(Resource.USERS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[UserRead]:
    users = await UserRepository(session).list_all()
    return [UserRead.model_validate(u) for u in users]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    _: User = Depends(require_permission(Resource.USERS, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    repo = UserRepository(session)
    if await repo.by_username(body.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nom d'utilisateur déjà pris",
        )
    try:
        user = await repo.create(
            username=body.username,
            email=body.email,
            password_hash=hash_password(body.password),
            full_name=body.full_name,
            role=body.role.value,
            is_active=True,
        )
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflit d'unicité",
        ) from exc
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    body: UserUpdate,
    current: User = Depends(require_permission(Resource.USERS, Action.UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    repo = UserRepository(session)
    user = await repo.by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )

    # Protection du dernier ADMIN actif
    admin_count = (await session.execute(
        select(func.count(User.id)).where(
            User.role == "ADMIN", User.is_active.is_(True)
        )
    )).scalar_one()

    would_remove_admin = (
        user.role == "ADMIN"
        and user.is_active
        and (
            (body.role is not None and body.role != Role.ADMIN)
            or (body.is_active is False)
        )
    )
    if would_remove_admin and admin_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de retirer le dernier ADMIN actif",
        )

    if body.full_name is not None:
        user.full_name = body.full_name
    if body.email is not None:
        user.email = body.email
    if body.role is not None:
        if user.id == current.id and body.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de retirer son propre rôle ADMIN",
            )
        user.role = body.role.value
    if body.is_active is not None:
        if user.id == current.id and body.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de se désactiver soi-même",
            )
        user.is_active = body.is_active
    if body.password is not None:
        user.password_hash = hash_password(body.password)

    await session.flush()
    return UserRead.model_validate(user)