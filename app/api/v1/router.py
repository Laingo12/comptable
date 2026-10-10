"""Agrégation des routeurs v1."""

from fastapi import APIRouter

from app.api.v1 import (
    associes,
    audit,
    auth,
    caisse_fg,
    charges,
    dashboard,
    eleves,
    exports,
    familles,
    imports,
    inscriptions,
    paiements,
    parametres,
    prelevements,
    referentiels,
    salaires,
    situation,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(audit.router)
api_router.include_router(referentiels.router)
api_router.include_router(parametres.router)
api_router.include_router(familles.router)
api_router.include_router(eleves.router)
api_router.include_router(inscriptions.router)
api_router.include_router(paiements.router)
api_router.include_router(situation.router)
api_router.include_router(associes.router)
api_router.include_router(charges.router)
api_router.include_router(salaires.router)
api_router.include_router(prelevements.router)
api_router.include_router(caisse_fg.router)
api_router.include_router(imports.router)
api_router.include_router(dashboard.router)
api_router.include_router(exports.router)