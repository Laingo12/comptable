"""functions and triggers: immutability, truncate, cancellation, derivation

Revision ID: 0002_functions_triggers
Revises: 0001_initial_tables
Create Date: 2026-10-07
"""
from __future__ import annotations

from alembic import op

revision = "0002_functions_triggers"
down_revision = "0001_initial_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================
    # Fonctions génériques
    # =========================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION forbid_mutation() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'Ledger immuable : % interdit sur %', TG_OP, TG_TABLE_NAME
            USING ERRCODE = 'restrict_violation';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION forbid_truncate() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'TRUNCATE interdit sur %', TG_TABLE_NAME
            USING ERRCODE = 'restrict_violation';
        END;
        $$ LANGUAGE plpgsql;
    """)

    # =========================================================
    # Triggers d'immuabilité (UPDATE / DELETE) sur les 5 ledgers + audit_log
    # =========================================================
    for table in (
        "paiements",
        "charges",
        "paiements_salaires",
        "prelevements",
        "caisse_fg_mouvements",
        "audit_log",
    ):
        op.execute(
            f"CREATE TRIGGER trg_{table}_immutable "
            f"BEFORE UPDATE OR DELETE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION forbid_mutation();"
        )

    # =========================================================
    # Triggers TRUNCATE (BEFORE TRUNCATE, FOR EACH STATEMENT)
    # =========================================================
    for table in (
        "paiements",
        "charges",
        "paiements_salaires",
        "prelevements",
        "caisse_fg_mouvements",
        "audit_log",
    ):
        op.execute(
            f"CREATE TRIGGER trg_{table}_truncate "
            f"BEFORE TRUNCATE ON {table} "
            f"FOR EACH STATEMENT EXECUTE FUNCTION forbid_truncate();"
        )

    # =========================================================
    # Trigger d'annulation paiements
    # =========================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION check_annulation_paiement() RETURNS trigger AS $$
        DECLARE o RECORD;
        BEGIN
          IF NEW.parent_paiement_id IS NULL THEN RETURN NEW; END IF;
          SELECT montant, inscription_id, type_paiement_id, mois_concerne_id
            INTO o FROM paiements WHERE id = NEW.parent_paiement_id;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'Paiement parent % introuvable', NEW.parent_paiement_id;
          END IF;
          IF NEW.montant <> -o.montant THEN
            RAISE EXCEPTION 'Montant incohérent : % <> -%', NEW.montant, o.montant;
          END IF;
          IF NEW.inscription_id   IS DISTINCT FROM o.inscription_id THEN
            RAISE EXCEPTION 'inscription_id différent du parent';
          END IF;
          IF NEW.type_paiement_id IS DISTINCT FROM o.type_paiement_id THEN
            RAISE EXCEPTION 'type_paiement_id différent du parent';
          END IF;
          IF NEW.mois_concerne_id IS DISTINCT FROM o.mois_concerne_id THEN
            RAISE EXCEPTION 'mois_concerne_id différent du parent';
          END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
    """)
    op.execute(
        "CREATE TRIGGER trg_paiements_annulation "
        "BEFORE INSERT ON paiements "
        "FOR EACH ROW EXECUTE FUNCTION check_annulation_paiement();"
    )

    # =========================================================
    # Trigger d'annulation charges
    # =========================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION check_annulation_charge() RETURNS trigger AS $$
        DECLARE o RECORD;
        BEGIN
          IF NEW.parent_charge_id IS NULL THEN RETURN NEW; END IF;
          SELECT montant, annee_scolaire_id, mois_id, categorie
            INTO o FROM charges WHERE id = NEW.parent_charge_id;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'Charge parente % introuvable', NEW.parent_charge_id;
          END IF;
          IF NEW.montant <> -o.montant THEN
            RAISE EXCEPTION 'Montant incohérent : % <> -%', NEW.montant, o.montant;
          END IF;
          IF NEW.annee_scolaire_id IS DISTINCT FROM o.annee_scolaire_id THEN
            RAISE EXCEPTION 'annee_scolaire_id différent du parent';
          END IF;
          IF NEW.mois_id IS DISTINCT FROM o.mois_id THEN
            RAISE EXCEPTION 'mois_id différent du parent';
          END IF;
          IF NEW.categorie IS DISTINCT FROM o.categorie THEN
            RAISE EXCEPTION 'categorie différente du parent';
          END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
    """)
    op.execute(
        "CREATE TRIGGER trg_charges_annulation "
        "BEFORE INSERT ON charges "
        "FOR EACH ROW EXECUTE FUNCTION check_annulation_charge();"
    )

    # =========================================================
    # Trigger d'annulation paiements_salaires
    # =========================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION check_annulation_psalaire() RETURNS trigger AS $$
        DECLARE o RECORD;
        BEGIN
          IF NEW.parent_paiement_salaire_id IS NULL THEN RETURN NEW; END IF;
          SELECT montant, employe_id, salaire_mensuel_id, type_part
            INTO o FROM paiements_salaires WHERE id = NEW.parent_paiement_salaire_id;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'Paiement salaire parent introuvable';
          END IF;
          IF NEW.montant <> -o.montant THEN
            RAISE EXCEPTION 'Montant incohérent : % <> -%', NEW.montant, o.montant;
          END IF;
          IF NEW.employe_id         IS DISTINCT FROM o.employe_id THEN
            RAISE EXCEPTION 'employe_id différent du parent';
          END IF;
          IF NEW.salaire_mensuel_id IS DISTINCT FROM o.salaire_mensuel_id THEN
            RAISE EXCEPTION 'salaire_mensuel_id différent du parent';
          END IF;
          IF NEW.type_part          IS DISTINCT FROM o.type_part THEN
            RAISE EXCEPTION 'type_part différent du parent';
          END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
    """)
    op.execute(
        "CREATE TRIGGER trg_psalaires_annulation "
        "BEFORE INSERT ON paiements_salaires "
        "FOR EACH ROW EXECUTE FUNCTION check_annulation_psalaire();"
    )

    # =========================================================
    # Trigger d'annulation caisse FG (sens opposé, même montant)
    # =========================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION check_annulation_caisse_fg() RETURNS trigger AS $$
        DECLARE o RECORD;
        BEGIN
          IF NEW.parent_mouvement_id IS NULL THEN RETURN NEW; END IF;
          SELECT montant, sens, annee_scolaire_id, mois_id
            INTO o FROM caisse_fg_mouvements WHERE id = NEW.parent_mouvement_id;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'Mouvement caisse FG parent introuvable';
          END IF;
          IF NEW.montant <> o.montant THEN
            RAISE EXCEPTION 'Montant incohérent : % <> %', NEW.montant, o.montant;
          END IF;
          IF NEW.sens = o.sens THEN
            RAISE EXCEPTION 'Le sens doit être opposé à celui du parent';
          END IF;
          IF NEW.annee_scolaire_id IS DISTINCT FROM o.annee_scolaire_id THEN
            RAISE EXCEPTION 'annee_scolaire_id différent du parent';
          END IF;
          IF NEW.mois_id IS DISTINCT FROM o.mois_id THEN
            RAISE EXCEPTION 'mois_id différent du parent';
          END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
    """)
    op.execute(
        "CREATE TRIGGER trg_caisse_fg_annulation "
        "BEFORE INSERT ON caisse_fg_mouvements "
        "FOR EACH ROW EXECUTE FUNCTION check_annulation_caisse_fg();"
    )

    # =========================================================
    # Trigger unique prelevements : dérivation + annulation fusionnées
    # (un seul BEFORE INSERT pour garantir l'ordre déterministe)
    # =========================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION derive_prelevement() RETURNS trigger AS $$
        DECLARE
          v_mois_id       BIGINT;
          v_annee         BIGINT;
          o               RECORD;
        BEGIN
          -- 1) Annulation : recopie stricte du parent, aucune dérivation.
          IF NEW.parent_prelevement_id IS NOT NULL THEN
            SELECT annee_scolaire_id, mois_id, associe_id, type, montant
              INTO o FROM prelevements WHERE id = NEW.parent_prelevement_id;
            IF NOT FOUND THEN
              RAISE EXCEPTION 'Prélèvement parent % introuvable', NEW.parent_prelevement_id;
            END IF;
            IF NEW.associe_id IS DISTINCT FROM o.associe_id THEN
              RAISE EXCEPTION 'associe_id différent du parent';
            END IF;
            IF NEW.type IS DISTINCT FROM o.type THEN
              RAISE EXCEPTION 'type différent du parent';
            END IF;
            IF NEW.montant <> -o.montant THEN
              RAISE EXCEPTION 'Montant incohérent : % <> -%', NEW.montant, o.montant;
            END IF;
            NEW.annee_scolaire_id := o.annee_scolaire_id;
            NEW.mois_id           := o.mois_id;
            RETURN NEW;
          END IF;

          -- 2) Année scolaire : si omise, on prend l'année active.
          IF NEW.annee_scolaire_id IS NULL THEN
            SELECT id INTO v_annee FROM annees_scolaires WHERE is_active = true LIMIT 1;
            IF v_annee IS NULL THEN
              RAISE EXCEPTION 'Aucune année scolaire active et annee_scolaire_id non fourni';
            END IF;
            NEW.annee_scolaire_id := v_annee;
          END IF;

          -- 3) Ligne non datée : forcer NON_DATE, pas de date.
          IF NEW.date_a_completer THEN
            SELECT id INTO v_mois_id FROM mois_scolaires
              WHERE annee_scolaire_id = NEW.annee_scolaire_id AND code = 'NON_DATE';
            IF v_mois_id IS NULL THEN
              RAISE EXCEPTION 'Mois NON_DATE introuvable pour l''année %', NEW.annee_scolaire_id;
            END IF;
            NEW.mois_id          := v_mois_id;
            NEW.date_prelevement := NULL;
            RETURN NEW;
          END IF;

          IF NEW.date_prelevement IS NULL THEN
            RAISE EXCEPTION 'date_prelevement obligatoire si date_a_completer = false';
          END IF;

          -- 4) Cherche le mois scolaire couvrant la date.
          SELECT id INTO v_mois_id FROM mois_scolaires
            WHERE annee_scolaire_id = NEW.annee_scolaire_id
              AND est_scolaire = true
              AND NEW.date_prelevement BETWEEN date_debut AND date_fin;

          -- 5) Hors année scolaire : bascule sur HORS_ANNEE (pas de rejet).
          IF v_mois_id IS NULL THEN
            SELECT id INTO v_mois_id FROM mois_scolaires
              WHERE annee_scolaire_id = NEW.annee_scolaire_id AND code = 'HORS_ANNEE';
            IF v_mois_id IS NULL THEN
              RAISE EXCEPTION 'Mois HORS_ANNEE introuvable pour l''année %', NEW.annee_scolaire_id;
            END IF;
          END IF;

          NEW.mois_id := v_mois_id;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
    """)
    op.execute(
        "CREATE TRIGGER trg_prelevements_01_derive "
        "BEFORE INSERT ON prelevements "
        "FOR EACH ROW EXECUTE FUNCTION derive_prelevement();"
    )

    # =========================================================
    # Trigger de dérivation du mois pour charges, paiements_salaires, caisse FG
    # (dates hors année → HORS_ANNEE, non daté → NON_DATE, mois_id recopié si annulation)
    # =========================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION derive_mois_operation() RETURNS trigger AS $$
        DECLARE
          v_mois_id BIGINT;
          v_mois_actuel BIGINT;
          v_col_date TEXT := TG_ARGV[0];   -- 'date_operation' | 'date_paiement'
          v_col_parent TEXT := TG_ARGV[1]; -- 'parent_charge_id' | 'parent_paiement_salaire_id' | 'parent_mouvement_id'
          v_col_a_completer TEXT := TG_ARGV[2]; -- 'date_a_completer'
          v_date DATE;
          v_a_completer BOOLEAN;
          v_parent BIGINT;
        BEGIN
          EXECUTE format('SELECT ($1).%I, ($1).%I, ($1).%I',
                         v_col_date, v_col_a_completer, v_col_parent)
            INTO v_date, v_a_completer, v_parent
            USING NEW;

          -- Annulation : on recopie le mois et l'année du parent
          IF v_parent IS NOT NULL THEN
            EXECUTE format('SELECT mois_id, annee_scolaire_id FROM %I WHERE id = $1',
                           TG_TABLE_NAME)
              INTO v_mois_id, v_mois_actuel
              USING v_parent;
            IF v_mois_id IS NULL THEN
              RAISE EXCEPTION 'Parent % introuvable pour %', v_parent, TG_TABLE_NAME;
            END IF;
            NEW.mois_id := v_mois_id;
            IF NEW.annee_scolaire_id IS NULL THEN
              NEW.annee_scolaire_id := v_mois_actuel;
            END IF;
            RETURN NEW;
          END IF;

          IF NEW.annee_scolaire_id IS NULL THEN
            SELECT id INTO v_mois_actuel FROM annees_scolaires WHERE is_active = true LIMIT 1;
            IF v_mois_actuel IS NULL THEN
              RAISE EXCEPTION 'Aucune année scolaire active';
            END IF;
            NEW.annee_scolaire_id := v_mois_actuel;
          END IF;

          IF v_a_completer THEN
            SELECT id INTO v_mois_id FROM mois_scolaires
              WHERE annee_scolaire_id = NEW.annee_scolaire_id AND code = 'NON_DATE';
            IF v_mois_id IS NULL THEN
              RAISE EXCEPTION 'Mois NON_DATE introuvable';
            END IF;
            EXECUTE format('NEW.%I := NULL', v_col_date);
            NEW.mois_id := v_mois_id;
            RETURN NEW;
          END IF;

          IF v_date IS NULL THEN
            RAISE EXCEPTION '% obligatoire si % = false', v_col_date, v_col_a_completer;
          END IF;

          SELECT id INTO v_mois_id FROM mois_scolaires
            WHERE annee_scolaire_id = NEW.annee_scolaire_id
              AND est_scolaire = true
              AND v_date BETWEEN date_debut AND date_fin;

          IF v_mois_id IS NULL THEN
            SELECT id INTO v_mois_id FROM mois_scolaires
              WHERE annee_scolaire_id = NEW.annee_scolaire_id AND code = 'HORS_ANNEE';
            IF v_mois_id IS NULL THEN
              RAISE EXCEPTION 'Mois HORS_ANNEE introuvable';
            END IF;
          END IF;

          NEW.mois_id := v_mois_id;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
    """)

    op.execute(
        "CREATE TRIGGER trg_charges_derive_mois "
        "BEFORE INSERT ON charges "
        "FOR EACH ROW EXECUTE FUNCTION derive_mois_operation("
        "'date_operation', 'parent_charge_id', 'date_a_completer');"
    )
    op.execute(
        "CREATE TRIGGER trg_psalaires_derive_mois "
        "BEFORE INSERT ON paiements_salaires "
        "FOR EACH ROW EXECUTE FUNCTION derive_mois_operation("
        "'date_paiement', 'parent_paiement_salaire_id', 'date_a_completer');"
    )
    op.execute(
        "CREATE TRIGGER trg_caisse_fg_derive_mois "
        "BEFORE INSERT ON caisse_fg_mouvements "
        "FOR EACH ROW EXECUTE FUNCTION derive_mois_operation("
        "'date_operation', 'parent_mouvement_id', 'date_a_completer');"
    )

    # =========================================================
    # Trigger de dérivation du mois pour paiements
    # (mois_concerne_id est le mois payé, indépendant de la date de paiement ;
    #  on force NON_DATE si date_a_completer, et on recopie le mois_concerne
    #  du parent en cas d'annulation. La date de paiement n'affecte PAS
    #  mois_concerne_id : elle sera utilisée par la vue v_encaissements_mensuels.)
    # =========================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION derive_paiement() RETURNS trigger AS $$
        DECLARE
          o RECORD;
        BEGIN
          IF NEW.parent_paiement_id IS NOT NULL THEN
            -- Annulation : recopie stricte
            SELECT annee_scolaire_id, inscription_id, type_paiement_id, mois_concerne_id
              INTO o FROM paiements WHERE id = NEW.parent_paiement_id;
            IF NOT FOUND THEN
              RAISE EXCEPTION 'Paiement parent % introuvable', NEW.parent_paiement_id;
            END IF;
            IF NEW.montant <> -(SELECT montant FROM paiements WHERE id = NEW.parent_paiement_id) THEN
              RAISE EXCEPTION 'Montant incohérent';
            END IF;
            NEW.annee_scolaire_id := o.annee_scolaire_id;
            NEW.inscription_id    := o.inscription_id;
            NEW.type_paiement_id  := o.type_paiement_id;
            NEW.mois_concerne_id  := o.mois_concerne_id;
            RETURN NEW;
          END IF;

          IF NEW.annee_scolaire_id IS NULL THEN
            SELECT id INTO NEW.annee_scolaire_id
              FROM annees_scolaires WHERE is_active = true LIMIT 1;
            IF NEW.annee_scolaire_id IS NULL THEN
              RAISE EXCEPTION 'Aucune année scolaire active';
            END IF;
          END IF;

          IF NEW.date_a_completer THEN
            NEW.date_paiement := NULL;
          ELSIF NEW.date_paiement IS NULL THEN
            RAISE EXCEPTION 'date_paiement obligatoire si date_a_completer = false';
          END IF;

          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
    """)
    op.execute(
        "CREATE TRIGGER trg_paiements_derive "
        "BEFORE INSERT ON paiements "
        "FOR EACH ROW EXECUTE FUNCTION derive_paiement();"
    )


def downgrade() -> None:
    # Retirer les triggers d'abord, puis les fonctions (ordre inverse)
    for table in (
        "paiements",
        "charges",
        "paiements_salaires",
        "prelevements",
        "caisse_fg_mouvements",
        "audit_log",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON {table};")
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_truncate  ON {table};")

    op.execute("DROP TRIGGER IF EXISTS trg_paiements_derive          ON paiements;")
    op.execute("DROP TRIGGER IF EXISTS trg_charges_derive_mois       ON charges;")
    op.execute("DROP TRIGGER IF EXISTS trg_psalaires_derive_mois     ON paiements_salaires;")
    op.execute("DROP TRIGGER IF EXISTS trg_caisse_fg_derive_mois     ON caisse_fg_mouvements;")
    op.execute("DROP TRIGGER IF EXISTS trg_prelevements_01_derive    ON prelevements;")

    op.execute("DROP TRIGGER IF EXISTS trg_paiements_annulation       ON paiements;")
    op.execute("DROP TRIGGER IF EXISTS trg_charges_annulation         ON charges;")
    op.execute("DROP TRIGGER IF EXISTS trg_psalaires_annulation       ON paiements_salaires;")
    op.execute("DROP TRIGGER IF EXISTS trg_caisse_fg_annulation       ON caisse_fg_mouvements;")

    op.execute("DROP FUNCTION IF EXISTS derive_paiement();")
    op.execute("DROP FUNCTION IF EXISTS derive_mois_operation();")
    op.execute("DROP FUNCTION IF EXISTS derive_prelevement();")
    op.execute("DROP FUNCTION IF EXISTS check_annulation_caisse_fg();")
    op.execute("DROP FUNCTION IF EXISTS check_annulation_psalaire();")
    op.execute("DROP FUNCTION IF EXISTS check_annulation_charge();")
    op.execute("DROP FUNCTION IF EXISTS check_annulation_paiement();")
    op.execute("DROP FUNCTION IF EXISTS forbid_truncate();")
    op.execute("DROP FUNCTION IF EXISTS forbid_mutation();")