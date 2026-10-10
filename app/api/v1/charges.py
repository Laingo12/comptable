"""Endpoints charges."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.charges import Charge
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.charges import ChargeRepository
from app.repositories.referentiels import ReferentielRepository
from app.schemas.charge import ChargeCreate, ChargeRead
from app.schemas.pagination import Page, parse_sort
from app.services import charges as svc

router = APIRouter(prefix="/charges", tags=["charges"])

SORTABLE = {
    "date_operation": Charge.date_operation,
    "montant": Charge.montant,
    "created_at": Charge.created_at,
}


class AnnulationCharge(BaseModel):
    motif: str = Field(min_length=1, max_length=500)


@router.get("", response_model=Page[ChargeRead])
async def list_charges(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    annee_scolaire_id: int | None = Query(None),
    mois_id: int | None = Query(None),
    categorie: str | None = Query(None, pattern="^(FIXE|VARIABLE|AUTRE)$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    include_annules: bool = Query(False),
    sort: str | None = Query(None),
    _: User = Depends(require_permission(Resource.CHARGES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Page[ChargeRead]:
    if annee_scolaire_id is None:
        annee = await ReferentielRepository(session).get_annee_active()
        if annee is None:
            raise HTTPException(404, "Aucune année scolaire active")
        annee_scolaire_id = annee.id
    rows, total = await ChargeRepository(session).list(
        page, page_size, annee_scolaire_id, mois_id, categorie,
        date_from, date_to, include_annules,
        parse_sort(sort, SORTABLE, "date_operation"),
    )
    return Page[ChargeRead](
        items=[ChargeRead.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=ChargeRead, status_code=status.HTTP_201_CREATED)
async def create_charge(
    body: ChargeCreate,
    current: User = Depends(require_permission(Resource.CHARGES, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> ChargeRead:
    try:
        obj = await svc.create(session, created_by=current.id, data=body.model_dump())
    except svc.ChargeError as exc:
        raise HTTPException(400, str(exc))
    await session.refresh(obj)
    return ChargeRead.model_validate(obj)


@router.get("/{charge_id}", response_model=ChargeRead)
async def get_charge(
    charge_id: int,
    _: User = Depends(require_permission(Resource.CHARGES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> ChargeRead:
    obj = await ChargeRepository(session).by_id(charge_id)
    if obj is None:
        raise HTTPException(404, "Charge introuvable")
    return ChargeRead.model_validate(obj)


@router.post("/{charge_id}/annuler", response_model=ChargeRead,
             status_code=status.HTTP_201_CREATED)
async def annuler_charge(
    charge_id: int,
    body: AnnulationCharge,
    current: User = Depends(require_permission(Resource.CHARGES, Action.ANNULER)),
    session: AsyncSession = Depends(get_session),
) -> ChargeRead:
    try:
        obj = await svc.annuler(
            session, charge_id=charge_id, created_by=current.id, motif=body.motif
        )
    except svc.ChargeError as exc:
        raise HTTPException(400, str(exc))
    await session.refresh(obj)
    return ChargeRead.model_validate(obj)