"""Service situation écolage : agrège v_ecolage_situation + paiements détaillés."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eleves import Eleve, Inscription
from app.models.paiements import Paiement
from app.models.referentiel import MoisScolaire, TypePaiement


def _as_int(v) -> int:
    if v is None:
        return 0
    if isinstance(v, Decimal):
        return int(v)
    return int(v)


async def _paiements_effectifs_par_mois(
    session: AsyncSession, inscription_id: int, type_code: str
) -> dict[int, list[Paiement]]:
    rows = (await session.execute(
        select(Paiement)
        .join(TypePaiement, TypePaiement.id == Paiement.type_paiement_id)
        .where(
            Paiement.inscription_id == inscription_id,
            TypePaiement.code == type_code,
            Paiement.parent_paiement_id.is_(None),
            ~Paiement.id.in_(
                select(Paiement.parent_paiement_id).where(
                    Paiement.parent_paiement_id.is_not(None)
                )
            ),
        )
    )).scalars().all()
    out: dict[int, list[Paiement]] = {}
    for p in rows:
        if p.mois_concerne_id is not None:
            out.setdefault(p.mois_concerne_id, []).append(p)
    return out


async def _sum_paiements_par_type(
    session: AsyncSession, inscription_id: int, type_code: str
) -> int:
    v = await session.scalar(text("""
        SELECT COALESCE(SUM(p.montant), 0)
        FROM paiements p
        JOIN types_paiement tp ON tp.id = p.type_paiement_id
        WHERE p.inscription_id = :iid
          AND tp.code = :code
          AND p.parent_paiement_id IS NULL
          AND NOT EXISTS (
            SELECT 1 FROM paiements a WHERE a.parent_paiement_id = p.id
          )
    """), {"iid": inscription_id, "code": type_code})
    return _as_int(v)


def _ordre_mois_de_date(
    d: date | None, mois_rows: list[MoisScolaire]
) -> int | None:
    """Retourne l'ordre du mois scolaire qui contient la date, ou None."""
    if d is None:
        return None
    for m in mois_rows:
        if m.date_debut and m.date_fin and m.date_debut <= d <= m.date_fin:
            return m.ordre
    return None


def _qualifier_paiement(
    p: Paiement,
    ordre_par_mois: dict[int, int],
    mois_rows: list[MoisScolaire],
) -> str:
    """AVANCE / RETARD selon la position du mois concerné par rapport au mois du paiement."""
    if p.mois_concerne_id is None:
        return "NORMAL"
    ordre_concerne = ordre_par_mois.get(p.mois_concerne_id)
    ordre_paiement = _ordre_mois_de_date(p.date_paiement, mois_rows)
    if ordre_concerne is None or ordre_paiement is None:
        return "NORMAL"
    if ordre_concerne > ordre_paiement:
        return "AVANCE"
    if ordre_concerne < ordre_paiement:
        return "RETARD"
    return "NORMAL"


async def situation_inscription(
    session: AsyncSession, inscription: Inscription
) -> dict:
    eleve = await session.scalar(select(Eleve).where(Eleve.id == inscription.eleve_id))
    if eleve is None:
        raise ValueError("Élève introuvable")

    # Liste ordonnée des mois scolaires de l'année
    mois_rows = (await session.execute(
        select(MoisScolaire)
        .where(
            MoisScolaire.annee_scolaire_id == inscription.annee_scolaire_id,
            MoisScolaire.est_scolaire.is_(True),
        )
        .order_by(MoisScolaire.ordre)
    )).scalars().all()
    ordre_par_mois = {m.id: m.ordre for m in mois_rows}
    mois_entree = next(
        (m for m in mois_rows if m.id == inscription.mois_entree_id), None
    )
    ordre_entree = mois_entree.ordre if mois_entree else 1

    paiements_par_mois = await _paiements_effectifs_par_mois(
        session, inscription.id, "ECOLAGE"
    )

    vue_rows = (await session.execute(text("""
        SELECT mois_id, mois_code, mois_libelle, mois_ordre,
               date_limite_paiement, du, paye, reste_du, statut, echu, en_retard
        FROM v_ecolage_situation
        WHERE inscription_id = :iid
        ORDER BY mois_ordre
    """), {"iid": inscription.id})).mappings().all()

    mois_out = []
    tot_du = 0
    tot_paye = 0
    for row in vue_rows:
        if row["mois_ordre"] < ordre_entree:
            continue
        paiements = paiements_par_mois.get(row["mois_id"], [])
        p_lignes = [
            {
                "id": p.id,
                "montant": _as_int(p.montant),
                "date_paiement": p.date_paiement,
                "mode_paiement_id": p.mode_paiement_id,
                "reference": p.reference,
                "qualificatif": _qualifier_paiement(p, ordre_par_mois, mois_rows),
            }
            for p in paiements
        ]
        du_i = _as_int(row["du"])
        paye_i = _as_int(row["paye"])
        reste_i = _as_int(row["reste_du"])
        tot_du += du_i
        tot_paye += paye_i
        mois_out.append({
            "mois_id": row["mois_id"],
            "code": row["mois_code"],
            "libelle": row["mois_libelle"],
            "ordre": row["mois_ordre"],
            "date_limite_paiement": row["date_limite_paiement"],
            "du": du_i,
            "paye": paye_i,
            "reste_du": reste_i,
            "statut": row["statut"],
            "echu": bool(row["echu"]),
            "en_retard": bool(row["en_retard"]),
            "paiements": p_lignes,
        })

    paye_inscr = await _sum_paiements_par_type(session, inscription.id, "INSCRIPTION")
    paye_fg = await _sum_paiements_par_type(session, inscription.id, "FRAIS_GENERAUX")

    def _simple(du: int, paye: int) -> dict:
        du = _as_int(du)
        paye = _as_int(paye)
        reste = max(0, du - paye)
        if paye <= 0:
            statut = "IMPAYE"
        elif reste > 0:
            statut = "PARTIEL"
        else:
            statut = "PAYE"
        return {"du": du, "paye": paye, "reste_du": reste, "statut": statut}

    droits = _simple(inscription.droit_inscription_du, paye_inscr)
    fg = _simple(inscription.frais_generaux_du, paye_fg)

    tot_du_global = tot_du + droits["du"] + fg["du"]
    tot_paye_global = tot_paye + droits["paye"] + fg["paye"]
    reste = max(0, tot_du_global - tot_paye_global)
    taux = round(100.0 * tot_paye_global / tot_du_global, 2) if tot_du_global > 0 else 0.0

    return {
        "eleve_id": eleve.id,
        "inscription_id": inscription.id,
        "annee_scolaire_id": inscription.annee_scolaire_id,
        "matricule": eleve.matricule,
        "nom": eleve.nom,
        "prenoms": eleve.prenoms,
        "niveau_id": inscription.niveau_id,
        "mois_entree_id": inscription.mois_entree_id,
        "ecolage_mensuel": _as_int(inscription.ecolage_mensuel),
        "remise_pct": _as_int(inscription.remise_pct),
        "droits_inscription": droits,
        "frais_generaux": fg,
        "mois": mois_out,
        "totaux": {
            "du": tot_du_global,
            "paye": tot_paye_global,
            "reste_du": reste,
            "taux_recouvrement": taux,
        },
    }