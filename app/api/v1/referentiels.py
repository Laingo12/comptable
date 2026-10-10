"""Endpoints référentiels : niveaux, mois, types, modes, années, grille, charges."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.repositories.referentiels import ReferentielRepository
from app.schemas.referentiel import (
    AnneeScolaireRead,
    ChargeCatalogueCreate,
    ChargeCatalogueRead,
    ChargeCatalogueUpdate,
    GrilleTarifaireRead,
    GrilleTarifaireUpsert,
    MoisScolaireRead,
    ModePaiementRead,
    NiveauRead,
    TypePaiementRead,
)

router = APIRouter(tags=["referentiels"])


# ----------------------- Niveaux -----------------------
@router.get("/niveaux", response_model=list[NiveauRead])
async def list_niveaux(
    _: User = Depends(require_permission(Resource.REFERENTIELS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[NiveauRead]:
    rows = await ReferentielRepository(session).list_niveaux()
    return [NiveauRead.model_validate(r) for r in rows]


# ----------------------- Mois scolaires -----------------------
@router.get("/mois-scolaires", response_model=list[MoisScolaireRead])
async def list_mois(
    annee_scolaire_id: int | None = Query(None),
    _: User = Depends(require_permission(Resource.REFERENTIELS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[MoisScolaireRead]:
    repo = ReferentielRepository(session)
    if annee_scolaire_id is None:
        annee = await repo.get_annee_active()
        if annee is None:
            raise HTTPException(status_code=404, detail="Aucune année scolaire active")
        annee_scolaire_id = annee.id
    rows = await repo.list_mois(annee_scolaire_id)
    return [MoisScolaireRead.model_validate(r) for r in rows]


# ----------------------- Types paiement -----------------------
@router.get("/types-paiement", response_model=list[TypePaiementRead])
async def list_types(
    _: User = Depends(require_permission(Resource.REFERENTIELS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[TypePaiementRead]:
    rows = await ReferentielRepository(session).list_types()
    return [TypePaiementRead.model_validate(r) for r in rows]


# ----------------------- Modes paiement -----------------------
@router.get("/modes-paiement", response_model=list[ModePaiementRead])
async def list_modes(
    _: User = Depends(require_permission(Resource.REFERENTIELS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[ModePaiementRead]:
    rows = await ReferentielRepository(session).list_modes()
    return [ModePaiementRead.model_validate(r) for r in rows]


# ----------------------- Années scolaires -----------------------
@router.get("/annees", response_model=list[AnneeScolaireRead])
async def list_annees(
    _: User = Depends(require_permission(Resource.ANNEES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[AnneeScolaireRead]:
    rows = await ReferentielRepository(session).list_annees()
    return [AnneeScolaireRead.model_validate(r) for r in rows]


@router.get("/annees/active", response_model=AnneeScolaireRead)
async def get_annee_active(
    _: User = Depends(require_permission(Resource.ANNEES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> AnneeScolaireRead:
    annee = await ReferentielRepository(session).get_annee_active()
    if annee is None:
        raise HTTPException(status_code=404, detail="Aucune année scolaire active")
    return AnneeScolaireRead.model_validate(annee)


# ----------------------- Grille tarifaire -----------------------
@router.get("/grille-tarifaire", response_model=list[GrilleTarifaireRead])
async def list_grille(
    annee_scolaire_id: int | None = Query(None),
    _: User = Depends(require_permission(Resource.REFERENTIELS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[GrilleTarifaireRead]:
    repo = ReferentielRepository(session)
    if annee_scolaire_id is None:
        annee = await repo.get_annee_active()
        if annee is None:
            raise HTTPException(status_code=404, detail="Aucune année scolaire active")
        annee_scolaire_id = annee.id
    rows = await repo.list_grille(annee_scolaire_id)
    return [GrilleTarifaireRead.model_validate(r) for r in rows]


@router.put("/grille-tarifaire/{annee_scolaire_id}/{niveau_id}",
            response_model=GrilleTarifaireRead)
async def upsert_grille(
    annee_scolaire_id: int,
    niveau_id: int,
    body: GrilleTarifaireUpsert,
    current: User = Depends(require_permission(Resource.REFERENTIELS, Action.UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> GrilleTarifaireRead:
    if body.niveau_id != niveau_id:
        raise HTTPException(status_code=400, detail="niveau_id incohérent")
    repo = ReferentielRepository(session)
    obj = await repo.get_grille(annee_scolaire_id, niveau_id)
    if obj is None:
        from app.models.parametres import GrilleTarifaire
        obj = GrilleTarifaire(
            annee_scolaire_id=annee_scolaire_id,
            niveau_id=niveau_id,
            ecolage_mensuel=body.ecolage_mensuel,
            droit_inscription=body.droit_inscription,
            frais_generaux=body.frais_generaux,
        )
        session.add(obj)
    else:
        obj.ecolage_mensuel = body.ecolage_mensuel
        obj.droit_inscription = body.droit_inscription
        obj.frais_generaux = body.frais_generaux
    await session.flush()
    return GrilleTarifaireRead.model_validate(obj)


# ----------------------- Charges catalogue -----------------------
@router.get("/charges-catalogue", response_model=list[ChargeCatalogueRead])
async def list_charges(
    annee_scolaire_id: int | None = Query(None),
    _: User = Depends(require_permission(Resource.REFERENTIELS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[ChargeCatalogueRead]:
    rows = await ReferentielRepository(session).list_charges(annee_scolaire_id)
    return [ChargeCatalogueRead.model_validate(r) for r in rows]


@router.post("/charges-catalogue", response_model=ChargeCatalogueRead,
             status_code=status.HTTP_201_CREATED)
async def create_charge(
    body: ChargeCatalogueCreate,
    _: User = Depends(require_permission(Resource.REFERENTIELS, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> ChargeCatalogueRead:
    from app.models.parametres import ChargeCatalogue
    obj = ChargeCatalogue(
        annee_scolaire_id=body.annee_scolaire_id,
        code=body.code,
        libelle=body.libelle,
        categorie=body.categorie,
        montant_previsionnel=body.montant_previsionnel,
        is_active=True,
    )
    session.add(obj)
    await session.flush()
    return ChargeCatalogueRead.model_validate(obj)


@router.patch("/charges-catalogue/{charge_id}", response_model=ChargeCatalogueRead)
async def update_charge(
    charge_id: int,
    body: ChargeCatalogueUpdate,
    _: User = Depends(require_permission(Resource.REFERENTIELS, Action.UPDATE)),
    session: AsyncSession = Depends(get_session),
) -> ChargeCatalogueRead:
    obj = await ReferentielRepository(session).get_charge(charge_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Charge introuvable")
    if body.libelle is not None:
        obj.libelle = body.libelle
    if body.categorie is not None:
        obj.categorie = body.categorie
    if body.montant_previsionnel is not None:
        obj.montant_previsionnel = body.montant_previsionnel
    if body.is_active is not None:
        obj.is_active = body.is_active
    await session.flush()
    return ChargeCatalogueRead.model_validate(obj)