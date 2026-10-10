"""Endpoints inscriptions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.eleves import Eleve, Inscription
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.eleves import EleveRepository, InscriptionRepository
from app.repositories.referentiels import ReferentielRepository
from app.schemas.eleve import InscriptionCreate, InscriptionRead, InscriptionUpdate
from app.schemas.pagination import Page, parse_sort
from app.services import inscriptions as svc

router = APIRouter(prefix="/inscriptions", tags=["inscriptions"])

SORTABLE = {
    "created_at": Inscription.created_at,
    "eleve_id": Inscription.eleve_id,
    "niveau_id": Inscription.niveau_id,
    "statut": Inscription.statut,
}


@router.get("", response_model=Page[InscriptionRead])
async def list_inscriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    annee_scolaire_id: int | None = Query(None),
    niveau_id: int | None = Query(None),
    statut: str | None = Query(None),
    eleve_id: int | None = Query(None),
    sort: str | None = Query(None),
    _: User = Depends(require_permission(Resource.INSCRIPTIONS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Page[InscriptionRead]:
    rows, total = await InscriptionRepository(session).list(
        page, page_size, annee_scolaire_id, niveau_id, statut, eleve_id,
        parse_sort(sort, SORTABLE, "created_at"),
    )
    return Page[InscriptionRead](
        items=[InscriptionRead.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=InscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_inscription(
    body: InscriptionCreate,
    _: User = Depends(require_permission(Resource.INSCRIPTIONS, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> InscriptionRead:
    annee = await ReferentielRepository(session).get_annee_active()
    if annee is None:
        raise HTTPException(400, "Aucune année scolaire active")

    eleve = await EleveRepository(session).by_id(body.eleve_id)
    if eleve is None:
        raise HTTPException(404, "Élève introuvable")

    # Unicité élève × année
    existing = await InscriptionRepository(session).by_eleve_annee(
        body.eleve_id, annee.id
    )
    if existing is not None:
        raise HTTPException(409, "Élève déjà inscrit pour cette année")

    defaults = await svc.compute_defaults_for_new(
        session, annee.id, body.niveau_id, eleve.famille_id,
    )
    data = {
        "eleve_id": body.eleve_id,
        "annee_scolaire_id": annee.id,
        "niveau_id": body.niveau_id,
        "mois_entree_id": body.mois_entree_id,
        "ecolage_mensuel": body.ecolage_mensuel if body.ecolage_mensuel is not None else defaults["ecolage_mensuel"],
        "remise_pct": body.remise_pct if body.remise_pct is not None else defaults["remise_pct"],
        "droit_inscription_du": body.droit_inscription_du if body.droit_inscription_du is not None else defaults["droit_inscription_du"],
        "frais_generaux_du": body.frais_generaux_du if body.frais_generaux_du is not None else defaults["frais_generaux_du"],
        "statut": "ACTIF",
    }
    try:
        obj = await InscriptionRepository(session).create(**data)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Conflit d'inscription") from exc

    if eleve.famille_id is not None:
        await svc.recompute_famille(session, eleve.famille_id, annee.id)
        await session.refresh(obj)
    return InscriptionRead.model_validate(obj)


@router.get("/{inscription_id}", response_model=InscriptionRead)
async def get_inscription(
    inscription_id: int,
    _: User = Depends(require_permission(Resource.INSCRIPTIONS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> InscriptionRead:
    obj = await InscriptionRepository(session).by_id(inscription_id)
    if obj is None:
        raise HTTPException(404, "Inscription introuvable")
    return InscriptionRead.model_validate(obj)


@router.patch("/{inscription_id}", response_model=InscriptionRead)
async def update_inscription(
    inscription_id: int,
    body: InscriptionUpdate,
    _: User = Depends(require_permission(Resource.INSCRIPTIONS, Action.UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> InscriptionRead:
    repo = InscriptionRepository(session)
    obj = await repo.by_id(inscription_id)
    if obj is None:
        raise HTTPException(404, "Inscription introuvable")

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    await session.flush()

    # Recompute famille si changement de statut
    if "statut" in data:
        eleve = await EleveRepository(session).by_id(obj.eleve_id)
        if eleve is not None and eleve.famille_id is not None:
            await svc.recompute_famille(session, eleve.famille_id, obj.annee_scolaire_id)
            await session.refresh(obj)

    return InscriptionRead.model_validate(obj)