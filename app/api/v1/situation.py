"""Endpoints situation écolage et fiche élève."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.eleves import EleveRepository, InscriptionRepository
from app.repositories.referentiels import ReferentielRepository
from app.schemas.situation import EleveSituation
from app.services import situation as svc

router = APIRouter(tags=["situation"])


@router.get("/inscriptions/{inscription_id}/situation", response_model=EleveSituation)
async def situation_inscription(
    inscription_id: int,
    _: User = Depends(require_permission(Resource.INSCRIPTIONS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> EleveSituation:
    ins = await InscriptionRepository(session).by_id(inscription_id)
    if ins is None:
        raise HTTPException(404, "Inscription introuvable")
    try:
        data = await svc.situation_inscription(session, ins)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return EleveSituation.model_validate(data)


@router.get("/eleves/{eleve_id}/situation", response_model=EleveSituation)
async def situation_eleve(
    eleve_id: int,
    annee_scolaire_id: int | None = None,
    _: User = Depends(require_permission(Resource.ELEVES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> EleveSituation:
    eleve = await EleveRepository(session).by_id(eleve_id)
    if eleve is None:
        raise HTTPException(404, "Élève introuvable")

    annee_id = annee_scolaire_id
    if annee_id is None:
        annee = await ReferentielRepository(session).get_annee_active()
        if annee is None:
            raise HTTPException(404, "Aucune année scolaire active")
        annee_id = annee.id

    ins = await InscriptionRepository(session).by_eleve_annee(eleve_id, annee_id)
    if ins is None:
        raise HTTPException(404, "Aucune inscription pour cet élève sur cette année")

    try:
        data = await svc.situation_inscription(session, ins)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return EleveSituation.model_validate(data)