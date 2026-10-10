"""Service dashboards : exploitation des vues + priorités Jessy / salaires."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.parametres import ParametreRepository


def _as_int(v) -> int:
    if v is None:
        return 0
    if isinstance(v, Decimal):
        return int(v)
    return int(v)


def _as_float(v) -> float:
    if v is None:
        return 0.0
    return float(v)


async def _get_param(session: AsyncSession, annee_id: int, cle: str, default=None):
    p = await ParametreRepository(session).get(annee_id, cle)
    if p is None:
        return default
    return p.valeur


# ------------------------------------------------------------------
# Dashboard mensuel
# ------------------------------------------------------------------
async def dashboard_mensuel(
    session: AsyncSession, *, annee_id: int, mois_id: int
) -> dict:
    # 1) Ligne de trésorerie mensuelle
    tre = (await session.execute(text("""
        SELECT * FROM v_tresorerie_solde
        WHERE annee_scolaire_id = :aid AND mois_id = :mid
    """), {"aid": annee_id, "mid": mois_id})).mappings().one_or_none()
    if tre is None:
        raise ValueError("Aucune donnée de trésorerie pour ce mois")

    mois_code = tre["code"]
    mois_libelle = tre["libelle"]
    ordre = tre["ordre"]

    # 2) Encaissements bruts par type (mois concerné)
    par_type = (await session.execute(text("""
        SELECT tp.id AS type_paiement_id, tp.code AS type_code,
               COALESCE(SUM(p.montant), 0) AS total
        FROM paiements p
        JOIN types_paiement tp ON tp.id = p.type_paiement_id
        WHERE p.annee_scolaire_id = :aid
          AND p.parent_paiement_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM paiements a WHERE a.parent_paiement_id = p.id)
          AND p.mois_concerne_id = :mid
        GROUP BY tp.id, tp.code
    """), {"aid": annee_id, "mid": mois_id})).mappings().all()

    # 3) Encaissements par mode (mois du paiement)
    par_mode = (await session.execute(text("""
        SELECT mp.id AS mode_paiement_id, mp.code AS mode_code,
               COALESCE(SUM(p.montant), 0) AS total
        FROM paiements p
        JOIN mois_scolaires m
          ON m.annee_scolaire_id = p.annee_scolaire_id
         AND m.est_scolaire = true
         AND p.date_paiement BETWEEN m.date_debut AND m.date_fin
        LEFT JOIN modes_paiement mp ON mp.id = p.mode_paiement_id
        WHERE p.annee_scolaire_id = :aid
          AND m.id = :mid
          AND p.parent_paiement_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM paiements a WHERE a.parent_paiement_id = p.id)
          AND p.date_a_completer = false
        GROUP BY mp.id, mp.code
    """), {"aid": annee_id, "mid": mois_id})).mappings().all()

    # 4) Encaissements jour par jour (mois du paiement) + cumul
    par_jour_rows = (await session.execute(text("""
        SELECT EXTRACT(DAY FROM p.date_paiement)::int AS jour,
               COALESCE(SUM(p.montant), 0) AS total
        FROM paiements p
        JOIN mois_scolaires m
          ON m.annee_scolaire_id = p.annee_scolaire_id
         AND m.est_scolaire = true
         AND p.date_paiement BETWEEN m.date_debut AND m.date_fin
        WHERE p.annee_scolaire_id = :aid
          AND m.id = :mid
          AND p.parent_paiement_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM paiements a WHERE a.parent_paiement_id = p.id)
          AND p.date_a_completer = false
        GROUP BY jour
        ORDER BY jour
    """), {"aid": annee_id, "mid": mois_id})).mappings().all()
    par_jour = []
    cumul = 0
    for r in par_jour_rows:
        cumul += _as_int(r["total"])
        par_jour.append({
            "jour": r["jour"],
            "total": _as_int(r["total"]),
            "cumul": cumul,
        })

    # 5) Compteurs écolage (mois concerné)
    compteurs = (await session.execute(text("""
        SELECT
          COALESCE(SUM(CASE WHEN statut = 'PAYE'    THEN 1 ELSE 0 END), 0) AS payes,
          COALESCE(SUM(CASE WHEN statut = 'PARTIEL' THEN 1 ELSE 0 END), 0) AS partiels,
          COALESCE(SUM(CASE WHEN statut = 'IMPAYE'  THEN 1 ELSE 0 END), 0) AS impayes,
          COALESCE(SUM(CASE WHEN en_retard          THEN 1 ELSE 0 END), 0) AS en_retard,
          COALESCE(SUM(du), 0)       AS du,
          COALESCE(SUM(paye), 0)     AS paye,
          COALESCE(SUM(reste_du), 0) AS reste
        FROM v_ecolage_situation
        WHERE annee_scolaire_id = :aid AND mois_id = :mid
    """), {"aid": annee_id, "mid": mois_id})).mappings().one()

    ecolage_attendu = _as_int(compteurs["du"])
    ecolage_recu = _as_int(compteurs["paye"])
    ecolage_reste = _as_int(compteurs["reste"])
    taux = round(100.0 * ecolage_recu / ecolage_attendu, 2) if ecolage_attendu > 0 else 0.0

    # 6) Salaires payés dans le mois (base caisse)
    salaires_info = (await session.execute(text("""
        SELECT
          COALESCE(SUM(CASE WHEN ps.type_part = 'AVANCE_70'
                            THEN ps.montant ELSE 0 END), 0) AS paye_70,
          COALESCE(SUM(CASE WHEN ps.type_part = 'SOLDE_30'
                            THEN ps.montant ELSE 0 END), 0) AS paye_30
        FROM paiements_salaires ps
        JOIN salaires_mensuels sm ON sm.id = ps.salaire_mensuel_id
        JOIN mois_scolaires m
          ON m.annee_scolaire_id = sm.annee_scolaire_id
         AND ps.date_paiement BETWEEN m.date_debut AND m.date_fin
        WHERE sm.annee_scolaire_id = :aid
          AND m.id = :mid
          AND ps.parent_paiement_salaire_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM paiements_salaires a
                          WHERE a.parent_paiement_salaire_id = ps.id)
    """), {"aid": annee_id, "mid": mois_id})).mappings().one()

    # Salaires dus du mois (70 / 30)
    salaires_dus = (await session.execute(text("""
        SELECT COALESCE(SUM(montant_brut), 0) AS brut
        FROM salaires_mensuels
        WHERE annee_scolaire_id = :aid AND mois_id = :mid
    """), {"aid": annee_id, "mid": mois_id})).mappings().one()
    brut_mois = _as_int(salaires_dus["brut"])
    du_70 = (brut_mois * 70 + 50) // 100
    du_30 = brut_mois - du_70

    prelevements_mois = _as_int(tre["prelevements_mois"])

    # Disponible pour les 70 % après Jessy et charges
    reserve_min = _as_int(await _get_param(session, annee_id, "reserve_minimale_caisse", 0))
    charges_m = _as_int(tre["charges"])
    ca_retenu = _as_int(tre["encaissements_retenus"])
    dispo_brut = ca_retenu - charges_m - prelevements_mois
    disponible_70 = max(0, dispo_brut - reserve_min)
    pct_payable = round(100.0 * min(disponible_70, du_70) / du_70, 2) if du_70 > 0 else 100.0
    manque_25 = max(0, du_70 - disponible_70)

    # 7) Comparatif réel/prévisionnel
    prev_rows = (await session.execute(text("""
        SELECT libelle, COALESCE(SUM(montant_previsionnel), 0) AS prev
        FROM charges_catalogue
        WHERE annee_scolaire_id = :aid AND is_active = true
        GROUP BY libelle
    """), {"aid": annee_id})).mappings().all()

    reel_rows = (await session.execute(text("""
        SELECT libelle, COALESCE(SUM(montant), 0) AS reel
        FROM charges
        WHERE annee_scolaire_id = :aid AND mois_id = :mid
          AND parent_charge_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM charges a WHERE a.parent_charge_id = charges.id)
        GROUP BY libelle
    """), {"aid": annee_id, "mid": mois_id})).mappings().all()
    reel_map = {r["libelle"]: _as_int(r["reel"]) for r in reel_rows}

    comparatif = []
    for p in prev_rows:
        prev = _as_int(p["prev"])
        reel = reel_map.get(p["libelle"], 0)
        comparatif.append({
            "libelle": p["libelle"],
            "reel": reel,
            "previsionnel": prev,
            "ecart": reel - prev,
        })

    def _somme_type(code: str) -> int:
        return _as_int(next((r["total"] for r in par_type if r["type_code"] == code), 0))

    return {
        "annee_scolaire_id": annee_id,
        "mois_id": mois_id,
        "mois_code": mois_code,
        "mois_libelle": mois_libelle,
        "ordre": ordre,
        "ca_ecolage": _somme_type("ECOLAGE"),
        "ca_inscription": _somme_type("INSCRIPTION"),
        "ca_frais_generaux": _somme_type("FRAIS_GENERAUX"),
        "ca_autre": _somme_type("AUTRE"),
        "ca_total_brut": _as_int(tre["encaissements_bruts"]),
        "ca_retenu": ca_retenu,
        "avances": _as_int(tre["avances"]),
        "retards_regularises": _as_int(tre["retards_regularises"]),
        "par_mode": [
            {"mode_paiement_id": r["mode_paiement_id"],
             "mode_code": r["mode_code"],
             "total": _as_int(r["total"])}
            for r in par_mode
        ],
        "par_type": [
            {"type_paiement_id": r["type_paiement_id"],
             "type_code": r["type_code"],
             "total": _as_int(r["total"])}
            for r in par_type
        ],
        "par_jour": par_jour,
        "ecolage_attendu": ecolage_attendu,
        "ecolage_recu": ecolage_recu,
        "ecolage_reste_du": ecolage_reste,
        "taux_recouvrement": taux,
        "compteurs": {
            "payes": _as_int(compteurs["payes"]),
            "partiels": _as_int(compteurs["partiels"]),
            "impayes": _as_int(compteurs["impayes"]),
            "en_retard": _as_int(compteurs["en_retard"]),
        },
                "charges": charges_m,
        "salaires_payes": _as_int(tre["salaires"]),
        "resultat_avant_prelevements": _as_int(tre["resultat_avant_prelevements"]),
        "prelevements_mois": prelevements_mois,
        "resultat_apres_prelevements": _as_int(tre["resultat_apres_prelevements"]),
        "tresorerie_debut": _as_int(tre["tresorerie_debut"]),
        "tresorerie_fin": _as_int(tre["tresorerie_fin"]),
        "jessy_prioritaire_10": prelevements_mois,
        "salaires": {
            "brut_total": brut_mois,
            "du_70": du_70,
            "du_30": du_30,
            "paye_70": _as_int(salaires_info["paye_70"]),
            "paye_30": _as_int(salaires_info["paye_30"]),
            "disponible_pour_70": disponible_70,
            "pct_payable_25": pct_payable,
            "somme_manquante_25": manque_25,
        },
        "comparatif": comparatif,
    }


# ------------------------------------------------------------------
# Dashboard annuel
# ------------------------------------------------------------------
async def dashboard_annuel(session: AsyncSession, *, annee_id: int) -> dict:
    annee = (await session.execute(text("""
        SELECT libelle FROM annees_scolaires WHERE id = :aid
    """), {"aid": annee_id})).scalar_one()

    effectif = (await session.execute(text("""
        SELECT COUNT(*) FROM inscriptions
        WHERE annee_scolaire_id = :aid AND statut = 'ACTIF'
    """), {"aid": annee_id})).scalar_one()

    ca = (await session.execute(text("""
        SELECT tp.code, COALESCE(SUM(p.montant), 0) AS total
        FROM paiements p
        JOIN types_paiement tp ON tp.id = p.type_paiement_id
        WHERE p.annee_scolaire_id = :aid
          AND p.parent_paiement_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM paiements a WHERE a.parent_paiement_id = p.id)
        GROUP BY tp.code
    """), {"aid": annee_id})).mappings().all()
    ca_map = {r["code"]: _as_int(r["total"]) for r in ca}

    tot = (await session.execute(text("""
        SELECT
          COALESCE(SUM(encaissements_retenus), 0) AS retenus,
          COALESCE(SUM(charges), 0)               AS charges,
          COALESCE(SUM(salaires), 0)              AS salaires,
          COALESCE(SUM(prelevements_mois), 0)     AS prelevements,
          COALESCE(SUM(resultat_apres_prelevements), 0) AS resultat
        FROM v_tresorerie_mensuelle
        WHERE annee_scolaire_id = :aid
    """), {"aid": annee_id})).mappings().one()

    tresorerie_init = _as_int(
        await _get_param(session, annee_id, "tresorerie_initiale", 0)
    )
    tresorerie_actuelle = tresorerie_init + _as_int(tot["resultat"])

    mois_rows = (await session.execute(text("""
        SELECT code, libelle, ordre, encaissements_retenus, charges, salaires,
               prelevements_mois, resultat_apres_prelevements, tresorerie_fin
        FROM v_tresorerie_solde
        WHERE annee_scolaire_id = :aid
        ORDER BY ordre
    """), {"aid": annee_id})).mappings().all()

    retards = (await session.execute(text("""
        SELECT COALESCE(SUM(reste_du), 0)
        FROM v_ecolage_situation
        WHERE annee_scolaire_id = :aid AND en_retard = true
    """), {"aid": annee_id})).scalar_one()

    # Avances perçues = somme des avances exposées par la vue mensuelle.
    avances_percues = 0
    for r in (await session.execute(text("""
        SELECT avances FROM v_encaissements_mensuels
        WHERE annee_scolaire_id = :aid
    """), {"aid": annee_id})).mappings().all():
        avances_percues += _as_int(r["avances"])

    fg_restants = (await session.execute(text("""
        SELECT COALESCE(SUM(reste_du), 0) FROM v_frais_generaux_situation
        WHERE annee_scolaire_id = :aid
    """), {"aid": annee_id})).scalar_one()
    droits_restants = (await session.execute(text("""
        SELECT COALESCE(SUM(reste_du), 0) FROM v_droits_inscription_situation
        WHERE annee_scolaire_id = :aid
    """), {"aid": annee_id})).scalar_one()

    # Somme manquante cumulée : Σ max(0, du_70 − disponible)
    somme_manquante = 0
    for r in mois_rows:
        salaires_mois = _as_int(r["salaires"])
        du_70 = (salaires_mois * 70 + 50) // 100
        dispo = _as_int(r["resultat_apres_prelevements"])
        if du_70 > dispo:
            somme_manquante += du_70 - dispo

    return {
        "annee_scolaire_id": annee_id,
        "libelle": annee,
        "effectif": int(effectif),
        "ca_ecolage": ca_map.get("ECOLAGE", 0),
        "ca_inscription": ca_map.get("INSCRIPTION", 0),
        "ca_frais_generaux": ca_map.get("FRAIS_GENERAUX", 0),
        "ca_autre": ca_map.get("AUTRE", 0),
        "ca_total_brut": sum(ca_map.values()),
        "ca_retenu": _as_int(tot["retenus"]),
        "verse_associes": _as_int(tot["prelevements"]),
        "retards_a_recouvrer": _as_int(retards),
        "avances_percues": avances_percues,
        "fg_restants_dus": _as_int(fg_restants),
        "droits_inscription_restants_dus": _as_int(droits_restants),
        "tresorerie_actuelle": tresorerie_actuelle,
        "somme_manquante_cumulee": somme_manquante,
        "mois": [
            {
                "mois_code": r["code"],
                "mois_libelle": r["libelle"],
                "ordre": r["ordre"],
                "ca_retenu": _as_int(r["encaissements_retenus"]),
                "charges": _as_int(r["charges"]),
                "salaires": _as_int(r["salaires"]),
                "prelevements": _as_int(r["prelevements_mois"]),
                "resultat_apres_prelevements": _as_int(r["resultat_apres_prelevements"]),
                "tresorerie_fin": _as_int(r["tresorerie_fin"]),
            }
            for r in mois_rows
        ],
    }