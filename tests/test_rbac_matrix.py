"""Matrice RBAC complète — chaque (rôle, ressource, action) est vérifiée."""

from __future__ import annotations

import pytest

from app.models.enums import Role
from app.permissions.rbac import Action, Resource, has_permission

EXPECTED_CAISSE_FG = {
    (Resource.CAISSE_FG, Action.READ),
    (Resource.CAISSE_FG, Action.CREATE),
    (Resource.CAISSE_FG, Action.ANNULER),
}


@pytest.mark.parametrize("resource", list(Resource))
@pytest.mark.parametrize("action", list(Action))
def test_admin_has_all(resource, action):
    assert has_permission(Role.ADMIN.value, resource, action) is True


@pytest.mark.parametrize("resource,action", sorted(EXPECTED_CAISSE_FG, key=str))
def test_caisse_fg_only_its_own(resource, action):
    assert has_permission(Role.CAISSE_FG.value, resource, action) is True


def test_caisse_fg_forbidden_elsewhere():
    assert has_permission(Role.CAISSE_FG.value, Resource.PAIEMENTS, Action.CREATE) is False
    assert has_permission(Role.CAISSE_FG.value, Resource.USERS, Action.READ) is False


def test_lecture_can_read_but_not_write():
    assert has_permission(Role.LECTURE.value, Resource.ELEVES, Action.READ) is True
    assert has_permission(Role.LECTURE.value, Resource.ELEVES, Action.CREATE) is False
    assert has_permission(Role.LECTURE.value, Resource.PAIEMENTS, Action.CREATE) is False
    assert has_permission(Role.LECTURE.value, Resource.USERS, Action.READ) is False


def test_saisie_can_create_paiements_not_users():
    assert has_permission(Role.SAISIE.value, Resource.PAIEMENTS, Action.CREATE) is True
    assert has_permission(Role.SAISIE.value, Resource.USERS, Action.READ) is False


def test_comptable_no_users_no_parametres():
    for r in Resource:
        for a in Action:
            if r == Resource.USERS or r == Resource.PARAMETRES:
                assert has_permission(Role.COMPTABLE.value, r, a) is False
            else:
                assert has_permission(Role.COMPTABLE.value, r, a) is True


def test_unknown_role_denied():
    assert has_permission("UNKNOWN", Resource.ELEVES, Action.READ) is False