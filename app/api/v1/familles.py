"""Endpoints familles."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.eleves import Famille
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.familles import FamilleRepository
from app.schemas.famille import FamilleCreate, FamilleRead, FamilleUpdate
from app.schemas.pagination import Page, parse_sort

router = APIRouter(prefix="/familles", tags=["familles"])

SORTABLE = {
    "nom": Famille.nom,
    "created_at": Famille.created_at,
    "updated_at": Famille.updated_at,
}


@router.get("", response_model=Page[FamilleRead])
async def list_familles(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    q: str | None = Query(None),
    sort: str | None = Query(None),
    _: User = Depends(require_permission(Resource.FAMILLES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Page[FamilleRead]:
    rows, total = await FamilleRepository(session).list(
        page, page_size, q, parse_sort(sort, SORTABLE, "nom")
    )
    return Page[FamilleRead](
        items=[FamilleRead.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=FamilleRead, status_code=status.HTTP_201_CREATED)
async def create_famille(
    body: FamilleCreate,
    _: User = Depends(require_permission(Resource.FAMILLES, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> FamilleRead:
    obj = await FamilleRepository(session).create(**body.model_dump())
    await session.refresh(obj)
    return FamilleRead.model_validate(obj)


@router.get("/{famille_id}", response_model=FamilleRead)
async def get_famille(
    famille_id: int,
    _: User = Depends(require_permission(Resource.FAMILLES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> FamilleRead:
    obj = await FamilleRepository(session).by_id(famille_id)
    if obj is None:
        raise HTTPException(404, "Famille introuvable")
    return FamilleRead.model_validate(obj)


@router.patch("/{famille_id}", response_model=FamilleRead)
async def update_famille(
    famille_id: int,
    body: FamilleUpdate,
    _: User = Depends(require_permission(Resource.FAMILLES, Action.UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> FamilleRead:
    obj = await FamilleRepository(session).by_id(famille_id)
    if obj is None:
        raise HTTPException(404, "Famille introuvable")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    await session.flush()
    await session.refresh(obj)
    return FamilleRead.model_validate(obj)