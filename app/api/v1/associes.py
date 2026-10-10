"""Endpoints associés."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.associes import AssocieRepository
from app.schemas.associe import AssocieCreate, AssocieRead, AssocieUpdate

router = APIRouter(prefix="/associes", tags=["associes"])


@router.get("", response_model=list[AssocieRead])
async def list_associes(
    actif_only: bool = False,
    _: User = Depends(require_permission(Resource.ASSOCIES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[AssocieRead]:
    rows = await AssocieRepository(session).list(actif_only=actif_only)
    return [AssocieRead.model_validate(r) for r in rows]


@router.post("", response_model=AssocieRead, status_code=status.HTTP_201_CREATED)
async def create_associe(
    body: AssocieCreate,
    _: User = Depends(require_permission(Resource.ASSOCIES, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> AssocieRead:
    try:
        obj = await AssocieRepository(session).create(**body.model_dump())
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Nom d'associé déjà pris") from exc
    await session.refresh(obj)
    return AssocieRead.model_validate(obj)


@router.patch("/{associe_id}", response_model=AssocieRead)
async def update_associe(
    associe_id: int,
    body: AssocieUpdate,
    _: User = Depends(require_permission(Resource.ASSOCIES, Action.UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> AssocieRead:
    obj = await AssocieRepository(session).by_id(associe_id)
    if obj is None:
        raise HTTPException(404, "Associé introuvable")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await session.flush()
    await session.refresh(obj)
    return AssocieRead.model_validate(obj)