"""Endpoints prélèvements."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.prelevements import Prelevement
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.prelevements import PrelevementRepository
from app.repositories.referentiels import ReferentielRepository
from app.schemas.pagination import Page, parse_sort
from app.schemas.prelevement import PrelevementCreate, PrelevementRead
from app.services import prelevements as svc

router = APIRouter(prefix="/prelevements", tags=["prelevements"])

SORTABLE = {
    "date_prelevement": Prelevement.date_prelevement,
    "montant": Prelevement.montant,
    "created_at": Prelevement.created_at,
}


class Annulation(BaseModel):
    motif: str = Field(min_length=1, max_length=500)


@router.get("", response_model=Page[PrelevementRead])
async def list_prelevements(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    annee_scolaire_id: int | None = Query(None),
    associe_id: int | None = Query(None),
    mois_id: int | None = Query(None),
    type: str | None = Query(None, pattern="^(RETRAIT|VERSEMENT_FIXE|SUPPLEMENT)$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    include_annules: bool = Query(False),
    sort: str | None = Query(None),
    _: User = Depends(require_permission(Resource.PRELEVEMENTS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Page[PrelevementRead]:
    if annee_scolaire_id is None:
        annee = await ReferentielRepository(session).get_annee_active()
        if annee is None:
            raise HTTPException(404, "Aucune année scolaire active")
        annee_scolaire_id = annee.id
    rows, total = await PrelevementRepository(session).list(
        page, page_size, annee_scolaire_id, associe_id, mois_id, type,
        date_from, date_to, include_annules,
        parse_sort(sort, SORTABLE, "date_prelevement"),
    )
    return Page[PrelevementRead](
        items=[PrelevementRead.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=PrelevementRead, status_code=status.HTTP_201_CREATED)
async def create_prelevement(
    body: PrelevementCreate,
    current: User = Depends(require_permission(Resource.PRELEVEMENTS, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> PrelevementRead:
    try:
        obj = await svc.create(session, created_by=current.id, data=body.model_dump())
    except svc.PrelevementError as exc:
        raise HTTPException(400, str(exc))
    await session.refresh(obj)
    return PrelevementRead.model_validate(obj)


@router.get("/{prelevement_id}", response_model=PrelevementRead)
async def get_prelevement(
    prelevement_id: int,
    _: User = Depends(require_permission(Resource.PRELEVEMENTS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> PrelevementRead:
    obj = await PrelevementRepository(session).by_id(prelevement_id)
    if obj is None:
        raise HTTPException(404, "Prélèvement introuvable")
    return PrelevementRead.model_validate(obj)


@router.post("/{prelevement_id}/annuler", response_model=PrelevementRead,
             status_code=status.HTTP_201_CREATED)
async def annuler_prelevement(
    prelevement_id: int,
    body: Annulation,
    current: User = Depends(require_permission(Resource.PRELEVEMENTS, Action.ANNULER)),
    session: AsyncSession = Depends(get_session),
) -> PrelevementRead:
    try:
        obj = await svc.annuler(
            session, prelevement_id=prelevement_id,
            created_by=current.id, motif=body.motif,
        )
    except svc.PrelevementError as exc:
        raise HTTPException(400, str(exc))
    await session.refresh(obj)
    return PrelevementRead.model_validate(obj)