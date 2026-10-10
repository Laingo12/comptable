"""Endpoints paiements."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.paiements import Paiement
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.paiements import PaiementRepository
from app.repositories.referentiels import ReferentielRepository
from app.schemas.pagination import Page, parse_sort
from app.schemas.paiement import AnnulationRequest, PaiementCreate, PaiementRead
from app.services import paiements as svc

router = APIRouter(prefix="/paiements", tags=["paiements"])

SORTABLE = {
    "date_paiement": Paiement.date_paiement,
    "montant": Paiement.montant,
    "created_at": Paiement.created_at,
}


@router.get("", response_model=Page[PaiementRead])
async def list_paiements(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    annee_scolaire_id: int | None = Query(None),
    inscription_id: int | None = Query(None),
    type_paiement_id: int | None = Query(None),
    mois_concerne_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    include_annules: bool = Query(False),
    sort: str | None = Query(None),
    _: User = Depends(require_permission(Resource.PAIEMENTS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Page[PaiementRead]:
    if annee_scolaire_id is None:
        annee = await ReferentielRepository(session).get_annee_active()
        if annee is None:
            raise HTTPException(404, "Aucune année scolaire active")
        annee_scolaire_id = annee.id

    rows, total = await PaiementRepository(session).list(
        page, page_size, annee_scolaire_id, inscription_id, type_paiement_id,
        mois_concerne_id, date_from, date_to, include_annules,
        parse_sort(sort, SORTABLE, "date_paiement"),
    )
    return Page[PaiementRead](
        items=[PaiementRead.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=PaiementRead, status_code=status.HTTP_201_CREATED)
async def create_paiement(
    body: PaiementCreate,
    current: User = Depends(require_permission(Resource.PAIEMENTS, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> PaiementRead:
    try:
        obj = await svc.create(session, created_by=current.id, data=body.model_dump())
    except svc.PaiementError as exc:
        raise HTTPException(400, str(exc))
    return PaiementRead.model_validate(obj)


@router.get("/{paiement_id}", response_model=PaiementRead)
async def get_paiement(
    paiement_id: int,
    _: User = Depends(require_permission(Resource.PAIEMENTS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> PaiementRead:
    obj = await PaiementRepository(session).by_id(paiement_id)
    if obj is None:
        raise HTTPException(404, "Paiement introuvable")
    return PaiementRead.model_validate(obj)


@router.post("/{paiement_id}/annuler", response_model=PaiementRead,
             status_code=status.HTTP_201_CREATED)
async def annuler_paiement(
    paiement_id: int,
    body: AnnulationRequest,
    current: User = Depends(require_permission(Resource.PAIEMENTS, Action.ANNULER)),
    session: AsyncSession = Depends(get_session),
) -> PaiementRead:
    try:
        obj = await svc.annuler(
            session, paiement_id=paiement_id,
            created_by=current.id, motif=body.motif,
        )
    except svc.PaiementError as exc:
        raise HTTPException(400, str(exc))
    return PaiementRead.model_validate(obj)