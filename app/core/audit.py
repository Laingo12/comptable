"""Capture d'audit : hooks SQLAlchemy + helpers de contexte."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event, insert
from sqlalchemy.orm import Mapper, object_session
from sqlalchemy import inspect as sa_inspect

from app.models.audit import AuditLog
from app.models.base import Base

# Colonnes recopiées dans before_state / after_state, par table.
# Liste blanche stricte : password_hash n'y figure jamais.
AUDIT_FIELDS: dict[str, tuple[str, ...]] = {
    "users": (
        "id", "username", "email", "full_name", "role", "is_active",
        "last_login_at", "version", "created_at", "updated_at",
    ),
    "refresh_tokens": ("id", "user_id", "expires_at", "revoked_at",
                        "created_at", "family_id"),
    "annees_scolaires": ("id", "libelle", "date_debut", "date_fin",
                          "is_active", "version"),
    "parametres": ("id", "annee_scolaire_id", "cle", "valeur", "version",
                    "updated_by", "updated_at"),
    "grille_tarifaire": ("id", "annee_scolaire_id", "niveau_id", "ecolage_mensuel",
                          "droit_inscription", "frais_generaux", "version"),
    "charges_catalogue": ("id", "annee_scolaire_id", "code", "libelle", "categorie",
                           "montant_previsionnel", "is_active", "version"),
    "niveaux": ("id", "code", "libelle", "ordre"),
    "mois_scolaires": ("id", "annee_scolaire_id", "code", "libelle", "ordre",
                        "date_debut", "date_fin", "date_limite_paiement",
                        "est_scolaire"),
    "types_paiement": ("id", "code", "libelle", "ordre"),
    "modes_paiement": ("id", "code", "libelle", "ordre"),
    "familles": ("id", "nom", "contact_principal", "telephone", "email",
                  "adresse", "notes", "version"),
    "eleves": ("id", "matricule", "nom", "prenoms", "sexe", "date_naissance",
                "famille_id", "version"),
    "inscriptions": ("id", "eleve_id", "annee_scolaire_id", "niveau_id",
                      "mois_entree_id", "ecolage_mensuel", "remise_pct",
                      "droit_inscription_du", "frais_generaux_du", "statut",
                      "date_sortie", "version"),
    "employes": ("id", "nom", "prenom", "poste", "salaire_mensuel",
                  "date_embauche", "date_sortie", "statut", "version"),
    "salaires_mensuels": ("id", "employe_id", "annee_scolaire_id", "mois_id",
                           "montant_brut", "notes"),
    "paiements": ("id", "annee_scolaire_id", "inscription_id", "type_paiement_id",
                   "mois_concerne_id", "montant", "date_paiement",
                   "date_a_completer", "mode_paiement_id", "reference",
                   "observation", "parent_paiement_id", "motif_annulation",
                   "created_by", "created_at"),
    "charges": ("id", "annee_scolaire_id", "mois_id", "charge_catalogue_id",
                 "libelle", "categorie", "montant", "date_operation",
                 "date_a_completer", "mode_paiement_id", "reference",
                 "observation", "parent_charge_id", "created_by", "created_at"),
    "paiements_salaires": ("id", "annee_scolaire_id", "employe_id",
                            "salaire_mensuel_id", "type_part", "montant",
                            "date_paiement", "date_a_completer",
                            "mode_paiement_id", "reference", "observation",
                            "parent_paiement_salaire_id", "created_by",
                            "created_at"),
    "associes": ("id", "nom", "plafond_mensuel", "versement_fixe_mensuel",
                  "versement_fixe_mois_debut_ordre", "is_active", "version"),
    "prelevements": ("id", "annee_scolaire_id", "associe_id", "mois_id", "type",
                      "montant", "date_prelevement", "date_a_completer",
                      "destinataire", "motif", "mode_paiement_id", "reference",
                      "parent_prelevement_id", "created_by", "created_at"),
    "caisse_fg_mouvements": ("id", "annee_scolaire_id", "mois_id", "sens",
                              "montant", "date_operation", "date_a_completer",
                              "libelle", "remarque", "mode_paiement_id",
                              "reference", "parent_mouvement_id", "created_by",
                              "created_at"),
}

_SKIP = {"audit_log", "alembic_version"}


def _snapshot(target: Any) -> dict | None:
    table = getattr(target, "__tablename__", None)
    if table is None or table in _SKIP:
        return None
    fields = AUDIT_FIELDS.get(table)
    if fields is None:
        return None
    out: dict[str, Any] = {}
    for f in fields:
        v = getattr(target, f, None)
        if v is None:
            continue
        if hasattr(v, "isoformat"):
            v = v.isoformat()
        out[f] = v
    return out


def _write(connection, target, action: str,
           before: dict | None, after: dict | None) -> None:
    table = getattr(target, "__tablename__", None)
    if table is None or table in _SKIP:
        return
    session = object_session(target)
    ctx = (session.info.get("audit_context") if session is not None else None) or {}
    connection.execute(
        insert(AuditLog).values(
            user_id=ctx.get("user_id"),
            action=action,
            entity_type=table,
            entity_id=str(getattr(target, "id", "") or "") or None,
            before_state=before,
            after_state=after,
            ip=ctx.get("ip"),
            user_agent=ctx.get("user_agent"),
        )
    )


def _on_insert(mapper: Mapper, connection, target) -> None:
    _write(connection, target, "INSERT", None, _snapshot(target))


def _on_update(mapper: Mapper, connection, target) -> None:
    insp = sa_inspect(target)
    before: dict[str, Any] = {}
    after: dict[str, Any] = {}
    fields = AUDIT_FIELDS.get(target.__tablename__, ())
    for f in fields:
        if f not in insp.attrs:
            continue
        hist = insp.attrs[f].history
        if not hist.has_changes():
            continue
        old = hist.deleted[0] if hist.deleted else None
        new = hist.added[0] if hist.added else None
        if hasattr(old, "isoformat"):
            old = old.isoformat()
        if hasattr(new, "isoformat"):
            new = new.isoformat()
        if old is not None:
            before[f] = old
        if new is not None:
            after[f] = new
    if not before and not after:
        return
    _write(connection, target, "UPDATE", before or None, after or None)


def _on_delete(mapper: Mapper, connection, target) -> None:
    _write(connection, target, "DELETE", _snapshot(target), None)


_REGISTERED = False


def register_audit_hooks() -> None:
    """Branche les événements mapper sur toutes les entités métier (idempotent)."""
    global _REGISTERED
    if _REGISTERED:
        return
    for mapper in Base.registry.mappers:
        cls: type = mapper.class_
        table = getattr(cls, "__tablename__", None)
        if table is None or table in _SKIP:
            continue
        if table not in AUDIT_FIELDS:
            continue
        event.listen(cls, "after_insert", _on_insert)
        event.listen(cls, "after_update", _on_update)
        event.listen(cls, "after_delete", _on_delete)
    _REGISTERED = True