"""Endpoints paramètres versionnés par année scolaire."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.parametres import ParametreRepository
from app.repositories.referentiels import ReferentielRepository
from app.schemas.parametre import ParametreRead, ParametreUpsert
from app.services import parametres as params_service

router = APIRouter(prefix="/parametres", tags=["parametres"])


async def _resolve_annee(session: AsyncSession, annee_scolaire_id: int | None) -> int:
    if annee_scolaire_id is not None:
        return annee_scolaire_id
    annee = await ReferentielRepository(session).get_annee_active()
    if annee is None:
        raise HTTPException(status_code=404, detail="Aucune année scolaire active")
    return annee.id


@router.get("", response_model=list[ParametreRead])
async def list_parametres(
    annee_scolaire_id: int | None = Query(None),
    _: User = Depends(require_permission(Resource.PARAMETRES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[ParametreRead]:
    aid = await _resolve_annee(session, annee_scolaire_id)
    rows = await ParametreRepository(session).list(aid)
    return [ParametreRead.model_validate(r) for r in rows]


@router.put("", response_model=ParametreRead)
async def upsert_parametre(
    body: ParametreUpsert,
    annee_scolaire_id: int | None = Query(None),
    current: User = Depends(require_permission(Resource.PARAMETRES, Action.UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> ParametreRead:
    aid = await _resolve_annee(session, annee_scolaire_id)
    try:
        obj = await params_service.upsert(
            session, aid, body.cle, body.valeur, body.description, current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await session.refresh(obj)
    return ParametreRead.model_validate(obj)