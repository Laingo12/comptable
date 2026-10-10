"""Endpoints élèves."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.eleves import Eleve
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.eleves import EleveRepository
from app.repositories.referentiels import ReferentielRepository
from app.schemas.eleve import EleveCreate, EleveRead, EleveUpdate
from app.schemas.pagination import Page, parse_sort

router = APIRouter(prefix="/eleves", tags=["eleves"])

SORTABLE = {
    "nom": Eleve.nom,
    "prenoms": Eleve.prenoms,
    "matricule": Eleve.matricule,
    "created_at": Eleve.created_at,
}


@router.get("", response_model=Page[EleveRead])
async def list_eleves(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    q: str | None = Query(None),
    famille_id: int | None = Query(None),
    sort: str | None = Query(None),
    _: User = Depends(require_permission(Resource.ELEVES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Page[EleveRead]:
    rows, total = await EleveRepository(session).list(
        page, page_size, q, famille_id,
        parse_sort(sort, SORTABLE, "nom"),
    )
    return Page[EleveRead](
        items=[EleveRead.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=EleveRead, status_code=status.HTTP_201_CREATED)
async def create_eleve(
    body: EleveCreate,
    _: User = Depends(require_permission(Resource.ELEVES, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> EleveRead:
    repo = EleveRepository(session)
    data = body.model_dump()
    if not data.get("matricule"):
        annee = await ReferentielRepository(session).get_annee_active()
        if annee is None:
            raise HTTPException(400, "Aucune année scolaire active")
        annee_debut = annee.date_debut.year
        data["matricule"] = await repo.next_matricule(annee_debut)
    try:
        obj = await repo.create(**data)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Matricule déjà pris") from exc
    await session.refresh(obj)
    return EleveRead.model_validate(obj)


@router.get("/{eleve_id}", response_model=EleveRead)
async def get_eleve(
    eleve_id: int,
    _: User = Depends(require_permission(Resource.ELEVES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> EleveRead:
    obj = await EleveRepository(session).by_id(eleve_id)
    if obj is None:
        raise HTTPException(404, "Élève introuvable")
    return EleveRead.model_validate(obj)


@router.patch("/{eleve_id}", response_model=EleveRead)
async def update_eleve(
    eleve_id: int,
    body: EleveUpdate,
    _: User = Depends(require_permission(Resource.ELEVES, Action.UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> EleveRead:
    obj = await EleveRepository(session).by_id(eleve_id)
    if obj is None:
        raise HTTPException(404, "Élève introuvable")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    await session.flush()
    await session.refresh(obj)
    return EleveRead.model_validate(obj)