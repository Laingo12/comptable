"""Matrice RBAC — la source de vérité unique pour les permissions."""

from __future__ import annotations

from enum import StrEnum

from app.models.enums import Role


class Resource(StrEnum):
    USERS = "users"
    PARAMETRES = "parametres"
    REFERENTIELS = "referentiels"
    ANNEES = "annees"
    FAMILLES = "familles"
    ELEVES = "eleves"
    INSCRIPTIONS = "inscriptions"
    EMPLOYES = "employes"
    SALAIRES_MENSUELS = "salaires_mensuels"
    PAIEMENTS = "paiements"
    CHARGES = "charges"
    PAIEMENTS_SALAIRES = "paiements_salaires"
    ASSOCIES = "associes"
    PRELEVEMENTS = "prelevements"
    CAISSE_FG = "caisse_fg"
    AUDIT_LOG = "audit_log"
    DASHBOARD = "dashboard"
    RAPPORTS = "rapports"
    EXPORTS = "exports"


class Action(StrEnum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ANNULER = "annuler"





def _all() -> set[tuple[Resource, Action]]:
    return {(r, a) for r in Resource for a in Action}


# Matrice explicite par rôle (pas de wildcard implicite)
_MATRIX: dict[str, set[tuple[Resource, Action]]] = {
    Role.ADMIN.value: _all(),

    Role.COMPTABLE.value: _all() - {
        (Resource.USERS, a) for a in Action
    } - {
        (Resource.PARAMETRES, a) for a in Action
    },

    Role.SAISIE.value: {
        (Resource.ELEVES, Action.READ),
        (Resource.INSCRIPTIONS, Action.READ),
        (Resource.REFERENTIELS, Action.READ),
        (Resource.PAIEMENTS, Action.CREATE),
        (Resource.PAIEMENTS, Action.READ),
        (Resource.CHARGES, Action.CREATE),
        (Resource.CHARGES, Action.READ),
        (Resource.CAISSE_FG, Action.CREATE),
        (Resource.CAISSE_FG, Action.READ),
        (Resource.DASHBOARD, Action.READ),
    },

    Role.CAISSE_FG.value: {
        (Resource.CAISSE_FG, Action.READ),
        (Resource.CAISSE_FG, Action.CREATE),
        (Resource.CAISSE_FG, Action.ANNULER),
    },

    Role.LECTURE.value: {
        (r, Action.READ) for r in Resource
        if r not in {Resource.USERS, Resource.AUDIT_LOG}
    },
}


def has_permission(role: str, resource: Resource, action: Action) -> bool:
    """Vérifie qu'un rôle possède une permission précise."""
    return (resource, action) in _MATRIX.get(role, set())


def assert_permission(role: str, resource: Resource, action: Action) -> None:
    """Lève PermissionError si le rôle n'a pas la permission."""
    if not has_permission(role, resource, action):
        raise PermissionError(
            f"Rôle {role} non autorisé pour {resource.value}:{action.value}"
        )