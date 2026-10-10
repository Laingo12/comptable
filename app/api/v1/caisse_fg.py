"""Endpoints caisse FG."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.caisse_fg import CaisseFgMouvement
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.caisse_fg import CaisseFgRepository
from app.repositories.referentiels import ReferentielRepository
from app.schemas.caisse_fg import CaisseFgCreate, CaisseFgRead
from app.schemas.pagination import Page, parse_sort
from app.services import caisse_fg as svc

router = APIRouter(prefix="/caisse-fg", tags=["caisse_fg"])

SORTABLE = {
    "date_operation": CaisseFgMouvement.date_operation,
    "montant": CaisseFgMouvement.montant,
    "created_at": CaisseFgMouvement.created_at,
}


class Annulation(BaseModel):
    motif: str = Field(min_length=1, max_length=500)


@router.get("", response_model=Page[CaisseFgRead])
async def list_caisse_fg(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    annee_scolaire_id: int | None = Query(None),
    mois_id: int | None = Query(None),
    sens: str | None = Query(None, pattern="^(ENTREE|SORTIE)$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    include_annules: bool = Query(False),
    sort: str | None = Query(None),
    _: User = Depends(require_permission(Resource.CAISSE_FG, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Page[CaisseFgRead]:
    if annee_scolaire_id is None:
        annee = await ReferentielRepository(session).get_annee_active()
        if annee is None:
            raise HTTPException(404, "Aucune année scolaire active")
        annee_scolaire_id = annee.id
    rows, total = await CaisseFgRepository(session).list(
        page, page_size, annee_scolaire_id, mois_id, sens,
        date_from, date_to, include_annules,
        parse_sort(sort, SORTABLE, "date_operation"),
    )
    return Page[CaisseFgRead](
        items=[CaisseFgRead.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=CaisseFgRead, status_code=status.HTTP_201_CREATED)
async def create_caisse_fg(
    body: CaisseFgCreate,
    current: User = Depends(require_permission(Resource.CAISSE_FG, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> CaisseFgRead:
    try:
        obj = await svc.create(session, created_by=current.id, data=body.model_dump())
    except svc.CaisseFgError as exc:
        raise HTTPException(400, str(exc))
    await session.refresh(obj)
    return CaisseFgRead.model_validate(obj)


@router.get("/{mouvement_id}", response_model=CaisseFgRead)
async def get_caisse_fg(
    mouvement_id: int,
    _: User = Depends(require_permission(Resource.CAISSE_FG, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> CaisseFgRead:
    obj = await CaisseFgRepository(session).by_id(mouvement_id)
    if obj is None:
        raise HTTPException(404, "Mouvement introuvable")
    return CaisseFgRead.model_validate(obj)


@router.post("/{mouvement_id}/annuler", response_model=CaisseFgRead,
             status_code=status.HTTP_201_CREATED)
async def annuler_caisse_fg(
    mouvement_id: int,
    body: Annulation,
    current: User = Depends(require_permission(Resource.CAISSE_FG, Action.ANNULER)),
    session: AsyncSession = Depends(get_session),
) -> CaisseFgRead:
    try:
        obj = await svc.annuler(
            session, mouvement_id=mouvement_id,
            created_by=current.id, motif=body.motif,
        )
    except svc.CaisseFgError as exc:
        raise HTTPException(400, str(exc))
    await session.refresh(obj)
    return CaisseFgRead.model_validate(obj)