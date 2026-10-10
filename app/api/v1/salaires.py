"""Endpoints salaires : mensuels (catalogue) et paiements (ledger)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.salaires import PaiementSalaire
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.referentiels import ReferentielRepository
from app.repositories.salaires import (
    PaiementSalaireRepository,
    SalaireMensuelRepository,
)
from app.schemas.pagination import Page, parse_sort
from app.schemas.salaire import (
    PaiementSalaireCreate,
    PaiementSalaireRead,
    SalaireMensuelCreate,
    SalaireMensuelGenerer,
    SalaireMensuelRead,
)
from app.services import salaires as svc

router = APIRouter(tags=["salaires"])

SORTABLE_PA = {
    "date_paiement": PaiementSalaire.date_paiement,
    "montant": PaiementSalaire.montant,
    "created_at": PaiementSalaire.created_at,
}


class Annulation(BaseModel):
    motif: str = Field(min_length=1, max_length=500)


# ------------------ SalaireMensuel (catalogue) ------------------

@router.get("/salaires-mensuels", response_model=list[SalaireMensuelRead])
async def list_salaires_mensuels(
    annee_scolaire_id: int | None = Query(None),
    mois_id: int | None = Query(None),
    _: User = Depends(require_permission(Resource.SALAIRES_MENSUELS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[SalaireMensuelRead]:
    rows = await SalaireMensuelRepository(session).list(
        annee_scolaire_id, mois_id, [SalaireMensuelRepository.__init__ and None or __import__("app.models.personnel", fromlist=["SalaireMensuel"]).SalaireMensuel.id.asc()]
    )
    return [SalaireMensuelRead.model_validate(r) for r in rows]


@router.post("/salaires-mensuels", response_model=SalaireMensuelRead,
             status_code=status.HTTP_201_CREATED)
async def create_salaire_mensuel(
    body: SalaireMensuelCreate,
    _: User = Depends(require_permission(Resource.SALAIRES_MENSUELS, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> SalaireMensuelRead:
    annee = await ReferentielRepository(session).get_annee_active()
    if annee is None:
        raise HTTPException(400, "Aucune année scolaire active")
    existing = await SalaireMensuelRepository(session).by_employe_mois(
        body.employe_id, body.mois_id
    )
    if existing is not None:
        raise HTTPException(409, "Ligne salaire déjà présente pour cet employé et ce mois")
    obj = await SalaireMensuelRepository(session).create(
        employe_id=body.employe_id, annee_scolaire_id=annee.id,
        mois_id=body.mois_id, montant_brut=body.montant_brut, notes=body.notes,
    )
    return SalaireMensuelRead.model_validate(obj)


@router.post("/salaires-mensuels/generer")
async def generer_salaires(
    body: SalaireMensuelGenerer,
    _: User = Depends(require_permission(Resource.SALAIRES_MENSUELS, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        return await svc.generer_mensuel(
            session, mois_id=body.mois_id,
            annee_scolaire_id=body.annee_scolaire_id,
            montant_brut_par_defaut=body.montant_brut_par_defaut,
        )
    except svc.SalaireError as exc:
        raise HTTPException(400, str(exc))


# ------------------ PaiementSalaire (ledger) ------------------

@router.get("/paiements-salaires", response_model=Page[PaiementSalaireRead])
async def list_paiements_salaires(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    annee_scolaire_id: int | None = Query(None),
    employe_id: int | None = Query(None),
    salaire_mensuel_id: int | None = Query(None),
    include_annules: bool = Query(False),
    sort: str | None = Query(None),
    _: User = Depends(require_permission(Resource.PAIEMENTS_SALAIRES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Page[PaiementSalaireRead]:
    if annee_scolaire_id is None:
        annee = await ReferentielRepository(session).get_annee_active()
        if annee is None:
            raise HTTPException(404, "Aucune année scolaire active")
        annee_scolaire_id = annee.id
    rows, total = await PaiementSalaireRepository(session).list(
        page, page_size, annee_scolaire_id, employe_id, salaire_mensuel_id,
        include_annules, parse_sort(sort, SORTABLE_PA, "date_paiement"),
    )
    return Page[PaiementSalaireRead](
        items=[PaiementSalaireRead.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.post("/paiements-salaires", response_model=PaiementSalaireRead,
             status_code=status.HTTP_201_CREATED)
async def create_paiement_salaire(
    body: PaiementSalaireCreate,
    current: User = Depends(require_permission(Resource.PAIEMENTS_SALAIRES, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> PaiementSalaireRead:
    try:
        obj = await svc.create_paiement(
            session, created_by=current.id, data=body.model_dump()
        )
    except svc.SalaireError as exc:
        raise HTTPException(400, str(exc))
    await session.refresh(obj)
    return PaiementSalaireRead.model_validate(obj)


@router.post("/paiements-salaires/{paiement_id}/annuler",
             response_model=PaiementSalaireRead, status_code=status.HTTP_201_CREATED)
async def annuler_paiement_salaire(
    paiement_id: int,
    body: Annulation,
    current: User = Depends(require_permission(Resource.PAIEMENTS_SALAIRES, Action.ANNULER)),
    session: AsyncSession = Depends(get_session),
) -> PaiementSalaireRead:
    try:
        obj = await svc.annuler(
            session, paiement_id=paiement_id, created_by=current.id, motif=body.motif
        )
    except svc.SalaireError as exc:
        raise HTTPException(400, str(exc))
    await session.refresh(obj)
    return PaiementSalaireRead.model_validate(obj)