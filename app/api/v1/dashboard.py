"""Endpoints dashboards."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.referentiels import ReferentielRepository
from app.schemas.dashboard import DashboardAnnuel, DashboardMensuel
from app.services import dashboard as svc

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/mensuel", response_model=DashboardMensuel)
async def dashboard_mensuel(
    mois_id: int = Query(...),
    annee_scolaire_id: int | None = Query(None),
    _: User = Depends(require_permission(Resource.DASHBOARD, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> DashboardMensuel:
    aid = annee_scolaire_id
    if aid is None:
        annee = await ReferentielRepository(session).get_annee_active()
        if annee is None:
            raise HTTPException(404, "Aucune année scolaire active")
        aid = annee.id
    try:
        data = await svc.dashboard_mensuel(session, annee_id=aid, mois_id=mois_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return DashboardMensuel.model_validate(data)


@router.get("/annuel", response_model=DashboardAnnuel)
async def dashboard_annuel(
    annee_scolaire_id: int | None = Query(None),
    _: User = Depends(require_permission(Resource.DASHBOARD, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> DashboardAnnuel:
    aid = annee_scolaire_id
    if aid is None:
        annee = await ReferentielRepository(session).get_annee_active()
        if annee is None:
            raise HTTPException(404, "Aucune année scolaire active")
        aid = annee.id
    data = await svc.dashboard_annuel(session, annee_id=aid)
    return DashboardAnnuel.model_validate(data)