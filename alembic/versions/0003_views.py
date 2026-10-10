"""views and grants

Revision ID: 0003_views
Revises: 0002_functions_triggers
Create Date: 2026-10-07
"""
from __future__ import annotations

import os

from alembic import op

revision = "0003_views"
down_revision = "0002_functions_triggers"
branch_labels = None
depends_on = None

APP_USER = os.environ.get("POSTGRES_APP_USER", "smartkids_app")
TZ_EXPR = "(now() AT TIME ZONE 'Indian/Antananarivo')::date"


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE VIEW v_paiements_effectifs AS
        SELECT p.*
        FROM paiements p
        WHERE p.parent_paiement_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM paiements a WHERE a.parent_paiement_id = p.id);
    """)

    op.execute(f"""
        CREATE OR REPLACE VIEW v_ecolage_situation AS
        SELECT
          i.id                                     AS inscription_id,
          i.eleve_id,
          i.annee_scolaire_id,
          m.id                                     AS mois_id,
          m.code                                   AS mois_code,
          m.libelle                                AS mois_libelle,
          m.ordre                                  AS mois_ordre,
          m.date_limite_paiement,
          i.ecolage_mensuel                        AS du,
          COALESCE(p.paye, 0)                      AS paye,
          i.ecolage_mensuel - COALESCE(p.paye, 0)  AS reste_du,
          CASE
            WHEN COALESCE(p.paye, 0) = 0                 THEN 'IMPAYE'
            WHEN COALESCE(p.paye, 0) < i.ecolage_mensuel THEN 'PARTIEL'
            ELSE 'PAYE'
          END                                      AS statut,
          ({TZ_EXPR} >= m.date_limite_paiement)    AS echu,
          (({TZ_EXPR} >= m.date_limite_paiement)
            AND (i.ecolage_mensuel - COALESCE(p.paye, 0)) > 0) AS en_retard
        FROM inscriptions i
        JOIN mois_scolaires m
          ON m.annee_scolaire_id = i.annee_scolaire_id
         AND m.est_scolaire = true
         AND m.ordre >= (SELECT ordre FROM mois_scolaires WHERE id = i.mois_entree_id)
        LEFT JOIN LATERAL (
          SELECT SUM(pe.montant) AS paye
          FROM v_paiements_effectifs pe
          JOIN types_paiement tp ON tp.id = pe.type_paiement_id
          WHERE pe.inscription_id = i.id
            AND pe.mois_concerne_id = m.id
            AND tp.code = 'ECOLAGE'
        ) p ON true
        WHERE i.statut = 'ACTIF';
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_droits_inscription_situation AS
        SELECT
          i.id                                         AS inscription_id,
          i.eleve_id,
          i.annee_scolaire_id,
          i.droit_inscription_du                       AS du,
          COALESCE(p.paye, 0)                          AS paye,
          i.droit_inscription_du - COALESCE(p.paye, 0) AS reste_du,
          CASE
            WHEN COALESCE(p.paye, 0) = 0                      THEN 'IMPAYE'
            WHEN COALESCE(p.paye, 0) < i.droit_inscription_du THEN 'PARTIEL'
            ELSE 'PAYE'
          END                                          AS statut
        FROM inscriptions i
        LEFT JOIN LATERAL (
          SELECT SUM(pe.montant) AS paye
          FROM v_paiements_effectifs pe
          JOIN types_paiement tp ON tp.id = pe.type_paiement_id
          WHERE pe.inscription_id = i.id AND tp.code = 'INSCRIPTION'
        ) p ON true
        WHERE i.statut = 'ACTIF';
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_frais_generaux_situation AS
        SELECT
          i.id                                       AS inscription_id,
          i.eleve_id,
          i.annee_scolaire_id,
          i.frais_generaux_du                        AS du,
          COALESCE(p.paye, 0)                        AS paye,
          i.frais_generaux_du - COALESCE(p.paye, 0)  AS reste_du,
          CASE
            WHEN COALESCE(p.paye, 0) = 0                   THEN 'IMPAYE'
            WHEN COALESCE(p.paye, 0) < i.frais_generaux_du THEN 'PARTIEL'
            ELSE 'PAYE'
          END                                        AS statut
        FROM inscriptions i
        LEFT JOIN LATERAL (
          SELECT SUM(pe.montant) AS paye
          FROM v_paiements_effectifs pe
          JOIN types_paiement tp ON tp.id = pe.type_paiement_id
          WHERE pe.inscription_id = i.id AND tp.code = 'FRAIS_GENERAUX'
        ) p ON true
        WHERE i.statut = 'ACTIF';
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_charges_mensuelles AS
        SELECT
          c.annee_scolaire_id,
          c.mois_id,
          c.categorie,
          SUM(c.montant) AS total
        FROM charges c
        WHERE c.parent_charge_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM charges a WHERE a.parent_charge_id = c.id)
          AND c.date_a_completer = false
        GROUP BY c.annee_scolaire_id, c.mois_id, c.categorie;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_salaires_mensuels_dus AS
        SELECT
          sm.id                                          AS salaire_mensuel_id,
          sm.employe_id,
          sm.annee_scolaire_id,
          sm.mois_id,
          m.code                                         AS mois_code,
          m.est_scolaire,
          sm.montant_brut,
          ROUND(sm.montant_brut * 70.0 / 100.0)::BIGINT  AS du_avance_70,
          sm.montant_brut - ROUND(sm.montant_brut * 70.0 / 100.0)::BIGINT
                                                         AS du_solde_30,
          COALESCE(pa.paye, 0)                           AS paye_avance_70,
          COALESCE(ps.paye, 0)                           AS paye_solde_30
        FROM salaires_mensuels sm
        JOIN mois_scolaires m ON m.id = sm.mois_id
        LEFT JOIN LATERAL (
          SELECT SUM(montant) AS paye FROM paiements_salaires
          WHERE salaire_mensuel_id = sm.id AND type_part = 'AVANCE_70'
            AND parent_paiement_salaire_id IS NULL
            AND NOT EXISTS (SELECT 1 FROM paiements_salaires a
                            WHERE a.parent_paiement_salaire_id = paiements_salaires.id)
        ) pa ON true
        LEFT JOIN LATERAL (
          SELECT SUM(montant) AS paye FROM paiements_salaires
          WHERE salaire_mensuel_id = sm.id AND type_part = 'SOLDE_30'
            AND parent_paiement_salaire_id IS NULL
            AND NOT EXISTS (SELECT 1 FROM paiements_salaires a
                            WHERE a.parent_paiement_salaire_id = paiements_salaires.id)
        ) ps ON true;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_encaissements_mensuels AS
        SELECT
          pe.annee_scolaire_id,
          m.id                                                            AS mois_id,
          m.code                                                          AS mois_code,
          m.ordre,
          SUM(pe.montant)                                                 AS brut,
          SUM(CASE WHEN tp.code = 'ECOLAGE'        THEN pe.montant ELSE 0 END) AS ret_eco,
          SUM(CASE WHEN tp.code = 'INSCRIPTION'    THEN pe.montant ELSE 0 END) AS ret_droits,
          SUM(CASE WHEN tp.code = 'FRAIS_GENERAUX' THEN pe.montant ELSE 0 END) AS ret_fg,
          SUM(CASE WHEN tp.code = 'AUTRE'          THEN pe.montant ELSE 0 END) AS autre,
          SUM(CASE
                WHEN tp.code = 'ECOLAGE'
                 AND pe.mois_concerne_id IS NOT NULL
                 AND (SELECT est_scolaire FROM mois_scolaires
                       WHERE id = pe.mois_concerne_id) = true
                 AND (SELECT ordre FROM mois_scolaires
                       WHERE id = pe.mois_concerne_id) > m.ordre
                THEN pe.montant ELSE 0 END)                               AS avances,
          SUM(CASE
                WHEN tp.code = 'ECOLAGE'
                 AND pe.mois_concerne_id IS NOT NULL
                 AND (SELECT est_scolaire FROM mois_scolaires
                       WHERE id = pe.mois_concerne_id) = true
                 AND (SELECT ordre FROM mois_scolaires
                       WHERE id = pe.mois_concerne_id) < m.ordre
                THEN pe.montant ELSE 0 END)                               AS retards_regularises
        FROM v_paiements_effectifs pe
        JOIN types_paiement tp ON tp.id = pe.type_paiement_id
        JOIN mois_scolaires m
          ON m.annee_scolaire_id = pe.annee_scolaire_id
         AND m.est_scolaire = true
         AND pe.date_paiement BETWEEN m.date_debut AND m.date_fin
        WHERE pe.date_a_completer = false
        GROUP BY pe.annee_scolaire_id, m.id, m.code, m.ordre;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_prelevements_mensuels AS
        SELECT annee_scolaire_id, mois_id, SUM(montant) AS total
        FROM prelevements
        WHERE parent_prelevement_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM prelevements a
                          WHERE a.parent_prelevement_id = prelevements.id)
        GROUP BY annee_scolaire_id, mois_id;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_prelevements_associe_mois AS
        SELECT
          p.annee_scolaire_id,
          p.mois_id,
          p.associe_id,
          a.nom             AS associe_nom,
          a.plafond_mensuel,
          SUM(p.montant)    AS total,
          CASE
            WHEN a.plafond_mensuel IS NULL THEN 0
            WHEN SUM(p.montant) > a.plafond_mensuel
              THEN SUM(p.montant) - a.plafond_mensuel
            ELSE 0
          END               AS depassement
        FROM prelevements p
        JOIN associes a ON a.id = p.associe_id
        WHERE p.parent_prelevement_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM prelevements a2
                          WHERE a2.parent_prelevement_id = p.id)
        GROUP BY p.annee_scolaire_id, p.mois_id, p.associe_id, a.nom, a.plafond_mensuel;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_a_completer AS
        SELECT 'paiement'::text AS source, id AS ref, annee_scolaire_id, montant, created_at
          FROM paiements            WHERE date_a_completer = true
        UNION ALL
        SELECT 'charge'::text, id, annee_scolaire_id, montant, created_at
          FROM charges              WHERE date_a_completer = true
        UNION ALL
        SELECT 'paiement_salaire'::text, id, annee_scolaire_id, montant, created_at
          FROM paiements_salaires   WHERE date_a_completer = true
        UNION ALL
        SELECT 'prelevement'::text, id, annee_scolaire_id, montant, created_at
          FROM prelevements         WHERE date_a_completer = true
        UNION ALL
        SELECT 'caisse_fg'::text, id, annee_scolaire_id, montant, created_at
          FROM caisse_fg_mouvements WHERE date_a_completer = true;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_hors_periode AS
        SELECT 'paiement'::text AS source, p.id AS ref, p.annee_scolaire_id,
               p.date_paiement AS date_op, p.montant
          FROM v_paiements_effectifs p
         WHERE p.date_paiement IS NOT NULL
           AND NOT EXISTS (
             SELECT 1 FROM mois_scolaires m
             WHERE m.annee_scolaire_id = p.annee_scolaire_id
               AND m.est_scolaire = true
               AND p.date_paiement BETWEEN m.date_debut AND m.date_fin
           )
        UNION ALL
        SELECT 'paiement_salaire'::text, ps.id, sm.annee_scolaire_id,
               ps.date_paiement, ps.montant
          FROM paiements_salaires ps
          JOIN salaires_mensuels sm ON sm.id = ps.salaire_mensuel_id
         WHERE ps.parent_paiement_salaire_id IS NULL
           AND NOT EXISTS (SELECT 1 FROM paiements_salaires a
                           WHERE a.parent_paiement_salaire_id = ps.id)
           AND ps.date_paiement IS NOT NULL
           AND NOT EXISTS (
             SELECT 1 FROM mois_scolaires m
             WHERE m.annee_scolaire_id = sm.annee_scolaire_id
               AND m.est_scolaire = true
               AND ps.date_paiement BETWEEN m.date_debut AND m.date_fin
           )
        UNION ALL
        SELECT 'prelevement'::text, p.id, p.annee_scolaire_id,
               p.date_prelevement, p.montant
          FROM prelevements p
          JOIN mois_scolaires m ON m.id = p.mois_id
         WHERE p.parent_prelevement_id IS NULL
           AND NOT EXISTS (SELECT 1 FROM prelevements a
                           WHERE a.parent_prelevement_id = p.id)
           AND m.code = 'HORS_ANNEE';
    """)

    # ------------------------------------------------------------------
    # v_tresorerie_mensuelle — bool_or remplace max sur booléen
    # ------------------------------------------------------------------
    op.execute(f"""
        CREATE OR REPLACE VIEW v_tresorerie_mensuelle AS
        WITH params AS (
          SELECT annee_scolaire_id,
                 bool_or(CASE WHEN cle='inclure_droits_inscription_part_jessy'
                              THEN (valeur #>> '{{}}')::boolean END) AS opt_droits,
                 bool_or(CASE WHEN cle='inclure_frais_generaux_part_jessy'
                              THEN (valeur #>> '{{}}')::boolean END) AS opt_fg,
                 MAX(CASE WHEN cle='reliquat_salaires_30_precedent'
                          THEN (valeur #>> '{{}}')::bigint  END) AS reliquat_sept
          FROM parametres
          GROUP BY annee_scolaire_id
        ),
        enc AS (SELECT * FROM v_encaissements_mensuels),
        charges_m AS (
          SELECT annee_scolaire_id, mois_id, SUM(total) AS total
          FROM v_charges_mensuelles GROUP BY annee_scolaire_id, mois_id
        ),
        salaires_caisse AS (
          SELECT ps.annee_scolaire_id,
                 m_paye.id AS mois_id,
                 SUM(ps.montant) AS total
          FROM paiements_salaires ps
          JOIN mois_scolaires m_paye
            ON m_paye.annee_scolaire_id = ps.annee_scolaire_id
           AND m_paye.est_scolaire = true
           AND ps.date_paiement BETWEEN m_paye.date_debut AND m_paye.date_fin
          WHERE ps.parent_paiement_salaire_id IS NULL
            AND NOT EXISTS (SELECT 1 FROM paiements_salaires a
                            WHERE a.parent_paiement_salaire_id = ps.id)
            AND ps.date_a_completer = false
          GROUP BY ps.annee_scolaire_id, m_paye.id
        ),
        prelev_m AS (
          SELECT annee_scolaire_id, mois_id, SUM(montant) AS total
          FROM prelevements
          WHERE parent_prelevement_id IS NULL
            AND NOT EXISTS (SELECT 1 FROM prelevements a
                            WHERE a.parent_prelevement_id = prelevements.id)
          GROUP BY annee_scolaire_id, mois_id
        )
        SELECT
          m.annee_scolaire_id,
          m.id AS mois_id,
          m.code, m.libelle, m.ordre,
          COALESCE(e.brut, 0)                              AS encaissements_bruts,
          COALESCE(e.ret_eco, 0)
            + CASE WHEN COALESCE(pa.opt_droits, false)
                   THEN COALESCE(e.ret_droits,0) ELSE 0 END
            + CASE WHEN COALESCE(pa.opt_fg, false)
                   THEN COALESCE(e.ret_fg,0) + COALESCE(e.autre,0)
                   ELSE 0 END                              AS encaissements_retenus,
          COALESCE(e.avances, 0)                           AS avances,
          COALESCE(e.retards_regularises, 0)               AS retards_regularises,
          COALESCE(c.total, 0)                             AS charges,
          COALESCE(s.total, 0)
            + CASE WHEN m.ordre = 1 THEN COALESCE(pa.reliquat_sept, 0) ELSE 0 END
                                                           AS salaires,
          (COALESCE(e.ret_eco, 0)
            + CASE WHEN COALESCE(pa.opt_droits, false)
                   THEN COALESCE(e.ret_droits,0) ELSE 0 END
            + CASE WHEN COALESCE(pa.opt_fg, false)
                   THEN COALESCE(e.ret_fg,0) + COALESCE(e.autre,0)
                   ELSE 0 END)
          - COALESCE(c.total, 0)
          - (COALESCE(s.total, 0)
             + CASE WHEN m.ordre = 1 THEN COALESCE(pa.reliquat_sept, 0) ELSE 0 END)
                                                           AS resultat_avant_prelevements,
          COALESCE(pr.total, 0)                            AS prelevements_mois,
          ((COALESCE(e.ret_eco, 0)
            + CASE WHEN COALESCE(pa.opt_droits, false)
                   THEN COALESCE(e.ret_droits,0) ELSE 0 END
            + CASE WHEN COALESCE(pa.opt_fg, false)
                   THEN COALESCE(e.ret_fg,0) + COALESCE(e.autre,0)
                   ELSE 0 END)
          - COALESCE(c.total, 0)
          - (COALESCE(s.total, 0)
             + CASE WHEN m.ordre = 1 THEN COALESCE(pa.reliquat_sept, 0) ELSE 0 END))
          - COALESCE(pr.total, 0)                          AS resultat_apres_prelevements
        FROM mois_scolaires m
        LEFT JOIN params           pa ON pa.annee_scolaire_id = m.annee_scolaire_id
        LEFT JOIN enc              e  ON e.annee_scolaire_id  = m.annee_scolaire_id
                                     AND e.mois_id            = m.id
        LEFT JOIN charges_m        c  ON c.annee_scolaire_id  = m.annee_scolaire_id
                                     AND c.mois_id            = m.id
        LEFT JOIN salaires_caisse  s  ON s.annee_scolaire_id  = m.annee_scolaire_id
                                     AND s.mois_id            = m.id
        LEFT JOIN prelev_m         pr ON pr.annee_scolaire_id = m.annee_scolaire_id
                                     AND pr.mois_id           = m.id
        WHERE m.est_scolaire = true;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_tresorerie_solde AS
        SELECT
          t.*,
          COALESCE(p0.tr_init, 0)
            + COALESCE(SUM(t.resultat_apres_prelevements) OVER (
                PARTITION BY t.annee_scolaire_id ORDER BY t.ordre
                ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0) AS tresorerie_debut,
          COALESCE(p0.tr_init, 0)
            + COALESCE(SUM(t.resultat_apres_prelevements) OVER (
                PARTITION BY t.annee_scolaire_id ORDER BY t.ordre
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS tresorerie_fin
        FROM v_tresorerie_mensuelle t
        LEFT JOIN LATERAL (
          SELECT (valeur #>> '{}')::bigint AS tr_init
          FROM parametres
          WHERE annee_scolaire_id = t.annee_scolaire_id
            AND cle = 'tresorerie_initiale'
        ) p0 ON true;
    """)

    op.execute(f"""
        DO $$
        DECLARE r RECORD;
        BEGIN
          FOR r IN
            SELECT table_schema, table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
              AND table_name LIKE 'v\\_%' ESCAPE '\\'
          LOOP
            EXECUTE format('GRANT SELECT ON %I.%I TO {APP_USER}',
                           r.table_schema, r.table_name);
          END LOOP;
        END $$;
    """)


def downgrade() -> None:
    for v in (
        "v_tresorerie_solde",
        "v_tresorerie_mensuelle",
        "v_hors_periode",
        "v_a_completer",
        "v_prelevements_associe_mois",
        "v_prelevements_mensuels",
        "v_encaissements_mensuels",
        "v_salaires_mensuels_dus",
        "v_charges_mensuelles",
        "v_frais_generaux_situation",
        "v_droits_inscription_situation",
        "v_ecolage_situation",
        "v_paiements_effectifs",
    ):
        op.execute(f"DROP VIEW IF EXISTS {v} CASCADE;")