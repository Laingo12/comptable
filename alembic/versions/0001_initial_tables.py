"""initial tables, indexes, and table/sequence privileges

Revision ID: 0001_initial_tables
Revises:
Create Date: 2026-10-07
"""
from __future__ import annotations

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial_tables"
down_revision = None
branch_labels = None
depends_on = None

APP_USER = os.environ.get("POSTGRES_APP_USER", "smartkids_app")


def upgrade() -> None:
    # =========================================================
    # Tables (ordre respectant les dépendances FK)
    # =========================================================

    # --- users -----------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("username", postgresql.CITEXT, nullable=False, unique=True),
        sa.Column("email", postgresql.CITEXT, nullable=True, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("full_name", sa.Text, nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "role IN ('ADMIN','COMPTABLE','SAISIE','CAISSE_FG','LECTURE')",
            name="chk_users_role",
        ),
    )

    # --- refresh_tokens --------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text, nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("ip", postgresql.INET, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # --- audit_log -------------------------------------------------------
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("entity_type", sa.Text, nullable=False),
        sa.Column("entity_id", sa.Text, nullable=True),
        sa.Column("before_state", postgresql.JSONB, nullable=True),
        sa.Column("after_state", postgresql.JSONB, nullable=True),
        sa.Column("ip", postgresql.INET, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "action IN ('INSERT','UPDATE','DELETE','LOGIN','LOGOUT','ANNULATION','EXPORT')",
            name="chk_audit_action",
        ),
    )

    # --- annees_scolaires ------------------------------------------------
    op.create_table(
        "annees_scolaires",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("libelle", sa.Text, nullable=False, unique=True),
        sa.Column("date_debut", sa.Date, nullable=False),
        sa.Column("date_fin", sa.Date, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("date_fin > date_debut", name="chk_annee_dates"),
    )

    # --- niveaux ---------------------------------------------------------
    op.create_table(
        "niveaux",
        sa.Column("id", sa.SmallInteger, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("libelle", sa.Text, nullable=False),
        sa.Column("ordre", sa.SmallInteger, nullable=False, unique=True),
    )

    # --- mois_scolaires --------------------------------------------------
    op.create_table(
        "mois_scolaires",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(12), nullable=False),
        sa.Column("libelle", sa.Text, nullable=False),
        sa.Column("ordre", sa.SmallInteger, nullable=False),
        sa.Column("date_debut", sa.Date, nullable=True),
        sa.Column("date_fin", sa.Date, nullable=True),
        sa.Column("date_limite_paiement", sa.Date, nullable=True),
        sa.Column("est_scolaire", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("ordre BETWEEN 1 AND 99", name="chk_mois_ordre"),
        sa.CheckConstraint(
            "(est_scolaire = true AND date_debut IS NOT NULL AND date_fin IS NOT NULL "
            " AND date_limite_paiement IS NOT NULL) OR (est_scolaire = false)",
            name="chk_mois_dates",
        ),
        sa.UniqueConstraint("annee_scolaire_id", "code", name="uq_mois_annee_code"),
        sa.UniqueConstraint("annee_scolaire_id", "ordre", name="uq_mois_annee_ordre"),
    )

    # --- types_paiement --------------------------------------------------
    op.create_table(
        "types_paiement",
        sa.Column("id", sa.SmallInteger, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("libelle", sa.Text, nullable=False),
        sa.Column("ordre", sa.SmallInteger, nullable=False),
    )

    # --- modes_paiement --------------------------------------------------
    op.create_table(
        "modes_paiement",
        sa.Column("id", sa.SmallInteger, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("libelle", sa.Text, nullable=False),
        sa.Column("ordre", sa.SmallInteger, nullable=False),
    )

    # --- parametres ------------------------------------------------------
    op.create_table(
        "parametres",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cle", sa.Text, nullable=False),
        sa.Column("valeur", postgresql.JSONB, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("updated_by", sa.BigInteger, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("annee_scolaire_id", "cle", name="uq_parametre"),
    )

    # --- grille_tarifaire ------------------------------------------------
    op.create_table(
        "grille_tarifaire",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id", ondelete="CASCADE"), nullable=False),
        sa.Column("niveau_id", sa.SmallInteger, sa.ForeignKey("niveaux.id"), nullable=False),
        sa.Column("ecolage_mensuel", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("droit_inscription", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("frais_generaux", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("annee_scolaire_id", "niveau_id", name="uq_grille"),
        sa.CheckConstraint("ecolage_mensuel >= 0", name="chk_grille_eco"),
        sa.CheckConstraint("droit_inscription >= 0", name="chk_grille_inscr"),
        sa.CheckConstraint("frais_generaux >= 0", name="chk_grille_fg"),
    )

    # --- charges_catalogue -----------------------------------------------
    op.create_table(
        "charges_catalogue",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id", ondelete="CASCADE"), nullable=True),
        sa.Column("code", sa.Text, nullable=True),
        sa.Column("libelle", sa.Text, nullable=False),
        sa.Column("categorie", sa.String(10), nullable=False),
        sa.Column("montant_previsionnel", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.CheckConstraint("categorie IN ('FIXE','VARIABLE','AUTRE')", name="chk_charges_cat"),
        sa.CheckConstraint("montant_previsionnel >= 0", name="chk_charges_prev"),
    )

    # --- familles --------------------------------------------------------
    op.create_table(
        "familles",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("nom", sa.Text, nullable=False),
        sa.Column("contact_principal", sa.Text, nullable=True),
        sa.Column("telephone", sa.Text, nullable=True),
        sa.Column("email", sa.Text, nullable=True),
        sa.Column("adresse", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # --- eleves ----------------------------------------------------------
    op.create_table(
        "eleves",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("matricule", sa.Text, nullable=False, unique=True),
        sa.Column("nom", sa.Text, nullable=False),
        sa.Column("prenoms", sa.Text, nullable=False),
        sa.Column("sexe", sa.CHAR(1), nullable=True),
        sa.Column("date_naissance", sa.Date, nullable=True),
        sa.Column("famille_id", sa.BigInteger, sa.ForeignKey("familles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("sexe IN ('M','F')", name="chk_eleve_sexe"),
    )

    # --- inscriptions ----------------------------------------------------
    op.create_table(
        "inscriptions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("eleve_id", sa.BigInteger, sa.ForeignKey("eleves.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("niveau_id", sa.SmallInteger, sa.ForeignKey("niveaux.id"), nullable=False),
        sa.Column("mois_entree_id", sa.BigInteger, sa.ForeignKey("mois_scolaires.id"), nullable=False),
        sa.Column("ecolage_mensuel", sa.BigInteger, nullable=False),
        sa.Column("remise_pct", sa.SmallInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("droit_inscription_du", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("frais_generaux_du", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("statut", sa.String(10), nullable=False, server_default=sa.text("'ACTIF'")),
        sa.Column("date_sortie", sa.Date, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("eleve_id", "annee_scolaire_id", name="uq_inscription_eleve_annee"),
        sa.CheckConstraint("ecolage_mensuel >= 0", name="chk_inscr_eco"),
        sa.CheckConstraint("remise_pct BETWEEN 0 AND 100", name="chk_inscr_remise"),
        sa.CheckConstraint("droit_inscription_du >= 0", name="chk_inscr_droits"),
        sa.CheckConstraint("frais_generaux_du >= 0", name="chk_inscr_fg"),
        sa.CheckConstraint("statut IN ('ACTIF','SORTI')", name="chk_inscr_statut"),
    )

    # --- employes --------------------------------------------------------
    op.create_table(
        "employes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("nom", sa.Text, nullable=False),
        sa.Column("prenom", sa.Text, nullable=False),
        sa.Column("poste", sa.Text, nullable=True),
        sa.Column("salaire_mensuel", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("date_embauche", sa.Date, nullable=True),
        sa.Column("date_sortie", sa.Date, nullable=True),
        sa.Column("statut", sa.String(10), nullable=False, server_default=sa.text("'ACTIF'")),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("salaire_mensuel >= 0", name="chk_employe_salaire"),
        sa.CheckConstraint("statut IN ('ACTIF','SORTI')", name="chk_employe_statut"),
    )

    # --- salaires_mensuels -----------------------------------------------
    op.create_table(
        "salaires_mensuels",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employe_id", sa.BigInteger, sa.ForeignKey("employes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id"), nullable=False),
        sa.Column("mois_id", sa.BigInteger, sa.ForeignKey("mois_scolaires.id"), nullable=False),
        sa.Column("montant_brut", sa.BigInteger, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.UniqueConstraint("employe_id", "mois_id", name="uq_salaire_mensuel"),
        sa.CheckConstraint("montant_brut >= 0", name="chk_sal_brut"),
    )

    # --- paiements -------------------------------------------------------
    op.create_table(
        "paiements",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("inscription_id", sa.BigInteger, sa.ForeignKey("inscriptions.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("type_paiement_id", sa.SmallInteger, sa.ForeignKey("types_paiement.id"), nullable=False),
        sa.Column("mois_concerne_id", sa.BigInteger, sa.ForeignKey("mois_scolaires.id"), nullable=True),
        sa.Column("montant", sa.BigInteger, nullable=False),
        sa.Column("date_paiement", sa.Date, nullable=True),
        sa.Column("date_a_completer", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("mode_paiement_id", sa.SmallInteger, sa.ForeignKey("modes_paiement.id"), nullable=True),
        sa.Column("reference", sa.Text, nullable=True),
        sa.Column("observation", sa.Text, nullable=True),
        sa.Column("parent_paiement_id", sa.BigInteger, sa.ForeignKey("paiements.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("motif_annulation", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "(parent_paiement_id IS NULL AND montant > 0) OR "
            "(parent_paiement_id IS NOT NULL AND montant < 0)",
            name="chk_paiements_signe",
        ),
        sa.CheckConstraint(
            "(date_paiement IS NOT NULL AND date_a_completer = false) OR "
            "(date_paiement IS NULL     AND date_a_completer = true)",
            name="chk_paiements_date",
        ),
    )

    # --- charges ---------------------------------------------------------
    op.create_table(
        "charges",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mois_id", sa.BigInteger, sa.ForeignKey("mois_scolaires.id"), nullable=False),
        sa.Column("charge_catalogue_id", sa.BigInteger, sa.ForeignKey("charges_catalogue.id"), nullable=True),
        sa.Column("libelle", sa.Text, nullable=False),
        sa.Column("categorie", sa.String(10), nullable=False),
        sa.Column("montant", sa.BigInteger, nullable=False),
        sa.Column("date_operation", sa.Date, nullable=True),
        sa.Column("date_a_completer", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("mode_paiement_id", sa.SmallInteger, sa.ForeignKey("modes_paiement.id"), nullable=True),
        sa.Column("reference", sa.Text, nullable=True),
        sa.Column("observation", sa.Text, nullable=True),
        sa.Column("parent_charge_id", sa.BigInteger, sa.ForeignKey("charges.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("categorie IN ('FIXE','VARIABLE','AUTRE')", name="chk_charges_categorie"),
        sa.CheckConstraint(
            "(parent_charge_id IS NULL AND montant > 0) OR "
            "(parent_charge_id IS NOT NULL AND montant < 0)",
            name="chk_charges_signe",
        ),
        sa.CheckConstraint(
            "(date_operation IS NOT NULL AND date_a_completer = false) OR "
            "(date_operation IS NULL     AND date_a_completer = true)",
            name="chk_charges_date",
        ),
    )

    # --- paiements_salaires ----------------------------------------------
    op.create_table(
        "paiements_salaires",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("employe_id", sa.BigInteger, sa.ForeignKey("employes.id"), nullable=False),
        sa.Column("salaire_mensuel_id", sa.BigInteger, sa.ForeignKey("salaires_mensuels.id"), nullable=False),
        sa.Column("type_part", sa.String(10), nullable=False),
        sa.Column("montant", sa.BigInteger, nullable=False),
        sa.Column("date_paiement", sa.Date, nullable=True),
        sa.Column("date_a_completer", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("mode_paiement_id", sa.SmallInteger, sa.ForeignKey("modes_paiement.id"), nullable=True),
        sa.Column("reference", sa.Text, nullable=True),
        sa.Column("observation", sa.Text, nullable=True),
        sa.Column("parent_paiement_salaire_id", sa.BigInteger, sa.ForeignKey("paiements_salaires.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("type_part IN ('AVANCE_70','SOLDE_30')", name="chk_psal_type_part"),
        sa.CheckConstraint(
            "(parent_paiement_salaire_id IS NULL AND montant > 0) OR "
            "(parent_paiement_salaire_id IS NOT NULL AND montant < 0)",
            name="chk_psalaires_signe",
        ),
        sa.CheckConstraint(
            "(date_paiement IS NOT NULL AND date_a_completer = false) OR "
            "(date_paiement IS NULL     AND date_a_completer = true)",
            name="chk_psalaires_date",
        ),
    )

    # --- associes --------------------------------------------------------
    op.create_table(
        "associes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("nom", sa.Text, nullable=False, unique=True),
        sa.Column("plafond_mensuel", sa.BigInteger, nullable=True),
        sa.Column("versement_fixe_mensuel", sa.BigInteger, nullable=True),
        sa.Column("versement_fixe_mois_debut_ordre", sa.SmallInteger, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("plafond_mensuel IS NULL OR plafond_mensuel >= 0", name="chk_associe_plafond"),
        sa.CheckConstraint("versement_fixe_mensuel IS NULL OR versement_fixe_mensuel >= 0", name="chk_associe_vf"),
        sa.CheckConstraint(
            "versement_fixe_mois_debut_ordre IS NULL "
            "OR versement_fixe_mois_debut_ordre BETWEEN 1 AND 99",
            name="chk_associe_vf_ordre",
        ),
    )

    # --- prelevements ----------------------------------------------------
    op.create_table(
        "prelevements",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("associe_id", sa.BigInteger, sa.ForeignKey("associes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mois_id", sa.BigInteger, sa.ForeignKey("mois_scolaires.id"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False, server_default=sa.text("'RETRAIT'")),
        sa.Column("montant", sa.BigInteger, nullable=False),
        sa.Column("date_prelevement", sa.Date, nullable=True),
        sa.Column("date_a_completer", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("destinataire", sa.Text, nullable=True),
        sa.Column("motif", sa.Text, nullable=True),
        sa.Column("mode_paiement_id", sa.SmallInteger, sa.ForeignKey("modes_paiement.id"), nullable=True),
        sa.Column("reference", sa.Text, nullable=True),
        sa.Column("parent_prelevement_id", sa.BigInteger, sa.ForeignKey("prelevements.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "type IN ('RETRAIT','VERSEMENT_FIXE','SUPPLEMENT')",
            name="chk_prel_type",
        ),
        sa.CheckConstraint(
            "(parent_prelevement_id IS NULL AND montant > 0) OR "
            "(parent_prelevement_id IS NOT NULL AND montant < 0)",
            name="chk_prel_signe",
        ),
        sa.CheckConstraint(
            "(date_prelevement IS NOT NULL AND date_a_completer = false) OR "
            "(date_prelevement IS NULL     AND date_a_completer = true)",
            name="chk_prel_date",
        ),
    )

    # --- caisse_fg_mouvements --------------------------------------------
    op.create_table(
        "caisse_fg_mouvements",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("annee_scolaire_id", sa.BigInteger, sa.ForeignKey("annees_scolaires.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mois_id", sa.BigInteger, sa.ForeignKey("mois_scolaires.id"), nullable=False),
        sa.Column("sens", sa.String(6), nullable=False),
        sa.Column("montant", sa.BigInteger, nullable=False),
        sa.Column("date_operation", sa.Date, nullable=True),
        sa.Column("date_a_completer", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("libelle", sa.Text, nullable=False),
        sa.Column("remarque", sa.Text, nullable=True),
        sa.Column("mode_paiement_id", sa.SmallInteger, sa.ForeignKey("modes_paiement.id"), nullable=True),
        sa.Column("reference", sa.Text, nullable=True),
        sa.Column("parent_mouvement_id", sa.BigInteger, sa.ForeignKey("caisse_fg_mouvements.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("sens IN ('ENTREE','SORTIE')", name="chk_fg_sens"),
        sa.CheckConstraint("montant > 0", name="chk_fg_montant"),
        sa.CheckConstraint(
            "(date_operation IS NOT NULL AND date_a_completer = false) OR "
            "(date_operation IS NULL     AND date_a_completer = true)",
            name="chk_fg_date",
        ),
    )

    # =========================================================
    # Index
    # =========================================================

    # users
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_active", "users", ["is_active"], postgresql_where=sa.text("is_active"))

    # refresh_tokens
    op.create_index("ix_refresh_user", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_expires", "refresh_tokens", ["expires_at"])

    # audit_log
    op.create_index("ix_audit_user_date", "audit_log", ["user_id", sa.text("created_at DESC")])
    op.create_index("ix_audit_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("ix_audit_date", "audit_log", [sa.text("created_at DESC")])

    # annees_scolaires
    op.create_index("uq_annee_active", "annees_scolaires", ["is_active"], unique=True, postgresql_where=sa.text("is_active"))

    # mois_scolaires
    op.create_index("ix_mois_scolaire", "mois_scolaires", ["annee_scolaire_id"], postgresql_where=sa.text("est_scolaire"))

    # charges_catalogue
    op.create_index("ix_charges_cat", "charges_catalogue", ["annee_scolaire_id", "categorie"])
    op.create_index("ix_charges_active", "charges_catalogue", ["is_active"], postgresql_where=sa.text("is_active"))

    # familles
    op.create_index("ix_famille_tel", "familles", ["telephone"])

    # eleves
    op.create_index("ix_eleves_nom", "eleves", ["nom", "prenoms"])
    op.create_index("ix_eleves_famille", "eleves", ["famille_id"])

    # inscriptions
    op.create_index("ix_inscr_annee_statut", "inscriptions", ["annee_scolaire_id", "statut"])
    op.create_index("ix_inscr_niveau", "inscriptions", ["niveau_id"])
    op.create_index("ix_inscr_mois_entree", "inscriptions", ["mois_entree_id"])

    # salaires_mensuels
    op.create_index("ix_sal_mois", "salaires_mensuels", ["mois_id"])
    op.create_index("ix_sal_employe", "salaires_mensuels", ["employe_id"])

    # paiements
    op.create_index("ix_paie_annee_date", "paiements", ["annee_scolaire_id", "date_paiement"])
    op.create_index("ix_paie_inscr_mois", "paiements", ["inscription_id", "mois_concerne_id"])
    op.create_index("ix_paie_type", "paiements", ["type_paiement_id"])
    op.create_index("ix_paie_parent", "paiements", ["parent_paiement_id"])
    op.create_index(
        "uq_paiements_annulation", "paiements", ["parent_paiement_id"],
        unique=True, postgresql_where=sa.text("parent_paiement_id IS NOT NULL"),
    )
    op.create_index(
        "ix_paie_a_completer", "paiements", ["date_a_completer"],
        postgresql_where=sa.text("date_a_completer"),
    )

    # charges
    op.create_index("ix_chg_annee_mois", "charges", ["annee_scolaire_id", "mois_id"])
    op.create_index("ix_chg_cat", "charges", ["categorie"])
    op.create_index("ix_chg_parent", "charges", ["parent_charge_id"])
    op.create_index(
        "uq_charges_annulation", "charges", ["parent_charge_id"],
        unique=True, postgresql_where=sa.text("parent_charge_id IS NOT NULL"),
    )
    op.create_index(
        "ix_chg_a_completer", "charges", ["date_a_completer"],
        postgresql_where=sa.text("date_a_completer"),
    )

    # paiements_salaires
    op.create_index("ix_psal_mois", "paiements_salaires", ["salaire_mensuel_id", "type_part"])
    op.create_index("ix_psal_parent", "paiements_salaires", ["parent_paiement_salaire_id"])
    op.create_index(
        "uq_psalaires_annulation", "paiements_salaires", ["parent_paiement_salaire_id"],
        unique=True, postgresql_where=sa.text("parent_paiement_salaire_id IS NOT NULL"),
    )
    op.create_index(
        "ix_psal_a_completer", "paiements_salaires", ["date_a_completer"],
        postgresql_where=sa.text("date_a_completer"),
    )

    # prelevements
    op.create_index("ix_prel_annee_mois", "prelevements", ["annee_scolaire_id", "mois_id"])
    op.create_index("ix_prel_associe", "prelevements", ["associe_id"])
    op.create_index("ix_prel_parent", "prelevements", ["parent_prelevement_id"])
    op.create_index(
        "uq_prelevements_annulation", "prelevements", ["parent_prelevement_id"],
        unique=True, postgresql_where=sa.text("parent_prelevement_id IS NOT NULL"),
    )
    op.create_index(
        "ix_prel_a_completer", "prelevements", ["date_a_completer"],
        postgresql_where=sa.text("date_a_completer"),
    )

    # caisse_fg_mouvements
    op.create_index("ix_fg_annee_mois", "caisse_fg_mouvements", ["annee_scolaire_id", "mois_id"])
    op.create_index("ix_fg_sens", "caisse_fg_mouvements", ["sens"])
    op.create_index("ix_fg_parent", "caisse_fg_mouvements", ["parent_mouvement_id"])
    op.create_index(
        "uq_fg_annulation", "caisse_fg_mouvements", ["parent_mouvement_id"],
        unique=True, postgresql_where=sa.text("parent_mouvement_id IS NOT NULL"),
    )
    op.create_index(
        "ix_fg_a_completer", "caisse_fg_mouvements", ["date_a_completer"],
        postgresql_where=sa.text("date_a_completer"),
    )

    # =========================================================
    # Privilèges (tables + séquences) — rôles déjà créés par db/init/01-roles.sql
    # =========================================================

    ledger_tables = (
        "paiements, charges, paiements_salaires, prelevements, "
        "caisse_fg_mouvements, audit_log"
    )
    mutable_tables = (
        "users, refresh_tokens, annees_scolaires, parametres, grille_tarifaire, "
        "charges_catalogue, niveaux, mois_scolaires, types_paiement, modes_paiement, "
        "familles, eleves, inscriptions, employes, salaires_mensuels, associes"
    )

    op.execute(f"GRANT SELECT, INSERT ON {ledger_tables} TO {APP_USER}")
    op.execute(f"REVOKE UPDATE, DELETE, TRUNCATE ON {ledger_tables} FROM {APP_USER}")

    op.execute(f"GRANT SELECT, INSERT, UPDATE ON {mutable_tables} TO {APP_USER}")

    op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {APP_USER}")


def downgrade() -> None:
    # Retirer les privilèges n'est pas indispensable au DROP, mais propre.
    ledger_tables = (
        "paiements, charges, paiements_salaires, prelevements, "
        "caisse_fg_mouvements, audit_log"
    )
    mutable_tables = (
        "users, refresh_tokens, annees_scolaires, parametres, grille_tarifaire, "
        "charges_catalogue, niveaux, mois_scolaires, types_paiement, modes_paiement, "
        "familles, eleves, inscriptions, employes, salaires_mensuels, associes"
    )
    op.execute(f"REVOKE ALL ON {ledger_tables} FROM {APP_USER}")
    op.execute(f"REVOKE ALL ON {mutable_tables} FROM {APP_USER}")

    # Tables (ordre inverse des FK)
    op.drop_table("caisse_fg_mouvements")
    op.drop_table("prelevements")
    op.drop_table("associes")
    op.drop_table("paiements_salaires")
    op.drop_table("charges")
    op.drop_table("paiements")
    op.drop_table("salaires_mensuels")
    op.drop_table("employes")
    op.drop_table("inscriptions")
    op.drop_table("eleves")
    op.drop_table("familles")
    op.drop_table("charges_catalogue")
    op.drop_table("grille_tarifaire")
    op.drop_table("parametres")
    op.drop_table("modes_paiement")
    op.drop_table("types_paiement")
    op.drop_table("mois_scolaires")
    op.drop_table("niveaux")
    op.drop_table("annees_scolaires")
    op.drop_table("audit_log")
    op.drop_table("refresh_tokens")
    op.drop_table("users")