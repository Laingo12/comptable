"""Bootstrap idempotent : référentiels, année 2026-2027, paramètres, ADMIN.

Appelé par `python -m app.seeds.cli` (local) ou par l'entrypoint Docker.
Refuse de démarrer si BOOTSTRAP_ADMIN_USERNAME / BOOTSTRAP_ADMIN_PASSWORD
ne sont pas fournis (contrôlé par `Settings`, qui exige ces champs).
"""

from __future__ import annotations

import logging
from datetime import date

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.associes import Associe
from app.models.parametres import (
    AnneeScolaire,
    ChargeCatalogue,
    GrilleTarifaire,
    Parametre,
)
from app.models.referentiel import (
    MoisScolaire,
    ModePaiement,
    Niveau,
    TypePaiement,
)
from app.models.user import User

logger = logging.getLogger(__name__)
_ph = PasswordHasher()

ANNEE_LIBELLE = "2026-2027"
ANNEE_DEBUT = date(2026, 9, 1)
ANNEE_FIN = date(2027, 6, 30)

NIVEAUX: list[tuple[str, str, int]] = [
    ("CRECHE", "Crèche", 1),
    ("TPS",    "TPS",    2),
    ("PS",     "PS",     3),
    ("MS",     "MS",     4),
    ("GS",     "GS",     5),
    ("CP",     "CP",     6),
    ("CE1",    "CE1",    7),
    ("CE2",    "CE2",    8),
    ("CM1",    "CM1",    9),
    ("CM2",    "CM2",   10),
]

TYPES_PAIEMENT: list[tuple[str, str, int]] = [
    ("ECOLAGE",        "Écolage",            1),
    ("INSCRIPTION",    "Droit d'inscription", 2),
    ("FRAIS_GENERAUX", "Frais généraux",     3),
    ("AUTRE",          "Autre recette",      4),
]

MODES_PAIEMENT: list[tuple[str, str, int]] = [
    ("ESPECES",     "Espèces",      1),
    ("MVOLA",       "MVola",        2),
    ("CHEQUE",      "Chèque",       3),
    ("VIREMENT",    "Virement",     4),
    ("NON_PRECISE", "Non précisé",  5),
]

# (code, libelle, ordre, date_debut, date_fin, date_limite_paiement)
MOIS: list[tuple[str, str, int, date, date, date]] = [
    ("2026-09", "Septembre 2026", 1,  date(2026, 9, 1),  date(2026, 9, 30),  date(2026, 9, 5)),
    ("2026-10", "Octobre 2026",   2,  date(2026, 10, 1), date(2026, 10, 31), date(2026, 10, 5)),
    ("2026-11", "Novembre 2026",  3,  date(2026, 11, 1), date(2026, 11, 30), date(2026, 11, 5)),
    ("2026-12", "Décembre 2026",  4,  date(2026, 12, 1), date(2026, 12, 31), date(2026, 12, 5)),
    ("2027-01", "Janvier 2027",   5,  date(2027, 1, 1),  date(2027, 1, 31),  date(2027, 1, 5)),
    ("2027-02", "Février 2027",   6,  date(2027, 2, 1),  date(2027, 2, 28),  date(2027, 2, 5)),
    ("2027-03", "Mars 2027",      7,  date(2027, 3, 1),  date(2027, 3, 31),  date(2027, 3, 5)),
    ("2027-04", "Avril 2027",     8,  date(2027, 4, 1),  date(2027, 4, 30),  date(2027, 4, 5)),
    ("2027-05", "Mai 2027",       9,  date(2027, 5, 1),  date(2027, 5, 31),  date(2027, 5, 5)),
    ("2027-06", "Juin 2027",     10,  date(2027, 6, 1),  date(2027, 6, 30),  date(2027, 6, 5)),
]

# Grille par défaut (Ariary) : (écolage mensuel, droit inscription, frais généraux)
GRILLE: dict[str, tuple[int, int, int]] = {
    "CRECHE": (100_000, 50_000, 0),
    "TPS":    (110_000, 50_000, 0),
    "PS":     (120_000, 50_000, 0),
    "MS":     (130_000, 50_000, 0),
    "GS":     (140_000, 50_000, 0),
    "CP":     (150_000, 60_000, 0),
    "CE1":    (160_000, 60_000, 0),
    "CE2":    (170_000, 60_000, 0),
    "CM1":    (180_000, 60_000, 0),
    "CM2":    (190_000, 60_000, 0),
}

CHARGES_CATALOGUE: list[tuple[str, str, str, int]] = [
    ("LOYER",         "Loyer",         "FIXE",     0),
    ("GYMNASE",       "Gymnase",       "FIXE",     0),
    ("PAMF",          "PAMF",          "FIXE",     0),
    ("FIBRE",         "Fibre",         "FIXE",     0),
    ("CANTINE",       "Cantine",       "FIXE",     0),
    ("JIRAMA",        "JIRAMA",        "VARIABLE", 0),
    ("CNAPS",         "CNaPS",         "VARIABLE", 0),
    ("FUNHECE",       "FUNHECE",       "VARIABLE", 0),
    ("PETITE_CAISSE", "Petite caisse", "VARIABLE", 0),
]

PARAMS: list[tuple[str, object]] = [
    ("annee_scolaire",                          "2026-2027"),
    ("devise",                                  "MGA"),
    ("jour_limite_paiement",                    5),
    ("remise_fratrie_pct",                      10),
    ("salaire_avance_pct",                      70),
    ("salaire_solde_pct",                       30),
    ("jour_salaire_avance",                     25),
    ("jour_salaire_solde",                      10),
    ("tresorerie_initiale",                     0),
    ("tresorerie_initiale_date",                "2026-09-01"),
    ("reliquat_salaires_30_precedent",          0),
    ("inclure_droits_inscription_part_jessy",   False),
    ("inclure_frais_generaux_part_jessy",       False),
]


async def _get_or_create(session: AsyncSession, model, defaults: dict, **lookups):
    stmt = select(model)
    for k, v in lookups.items():
        stmt = stmt.where(getattr(model, k) == v)
    existing = await session.scalar(stmt)
    if existing is not None:
        return existing, False
    obj = model(**{**lookups, **defaults})
    session.add(obj)
    await session.flush()
    return obj, True


async def bootstrap(session: AsyncSession) -> None:
    """Peuple la base si nécessaire. Idempotent."""
    settings = get_settings()

    # --- Référentiels -------------------------------------------------
    for code, libelle, ordre in NIVEAUX:
        await _get_or_create(session, Niveau, {"libelle": libelle, "ordre": ordre}, code=code)

    for code, libelle, ordre in TYPES_PAIEMENT:
        await _get_or_create(
            session, TypePaiement, {"libelle": libelle, "ordre": ordre}, code=code
        )

    for code, libelle, ordre in MODES_PAIEMENT:
        await _get_or_create(
            session, ModePaiement, {"libelle": libelle, "ordre": ordre}, code=code
        )

    # --- Année scolaire ----------------------------------------------
    annee, created = await _get_or_create(
        session,
        AnneeScolaire,
        {"date_debut": ANNEE_DEBUT, "date_fin": ANNEE_FIN, "is_active": True},
        libelle=ANNEE_LIBELLE,
    )
    if created:
        logger.info("Année scolaire %s créée", ANNEE_LIBELLE)

    # --- Mois scolaires (10 + NON_DATE + HORS_ANNEE) -----------------
    for code, libelle, ordre, d1, d2, dlim in MOIS:
        await _get_or_create(
            session, MoisScolaire,
            {"libelle": libelle, "ordre": ordre,
             "date_debut": d1, "date_fin": d2, "date_limite_paiement": dlim,
             "est_scolaire": True},
            annee_scolaire_id=annee.id, code=code,
        )

    await _get_or_create(
        session, MoisScolaire,
        {"libelle": "Non daté", "ordre": 99,
         "date_debut": None, "date_fin": None, "date_limite_paiement": None,
         "est_scolaire": False},
        annee_scolaire_id=annee.id, code="NON_DATE",
    )
    await _get_or_create(
        session, MoisScolaire,
        {"libelle": "Hors année", "ordre": 98,
         "date_debut": None, "date_fin": None, "date_limite_paiement": None,
         "est_scolaire": False},
        annee_scolaire_id=annee.id, code="HORS_ANNEE",
    )

    # --- Grille tarifaire --------------------------------------------
    niveaux_db = {n.code: n for n in (await session.scalars(select(Niveau))).all()}
    for code_niveau, (eco, inscr, fg) in GRILLE.items():
        n = niveaux_db[code_niveau]
        await _get_or_create(
            session, GrilleTarifaire,
            {"ecolage_mensuel": eco, "droit_inscription": inscr, "frais_generaux": fg},
            annee_scolaire_id=annee.id, niveau_id=n.id,
        )

    # --- Catalogue de charges ----------------------------------------
    for code, libelle, cat, prev in CHARGES_CATALOGUE:
        await _get_or_create(
            session, ChargeCatalogue,
            {"libelle": libelle, "categorie": cat,
             "montant_previsionnel": prev, "is_active": True},
            annee_scolaire_id=annee.id, code=code,
        )

    # --- Paramètres ---------------------------------------------------
    for cle, val in PARAMS:
        existing = await session.scalar(
            select(Parametre).where(
                Parametre.annee_scolaire_id == annee.id,
                Parametre.cle == cle,
            )
        )
        if existing is None:
            session.add(Parametre(annee_scolaire_id=annee.id, cle=cle, valeur=val))
            await session.flush()

    # --- Associée Jessy ----------------------------------------------
    jessy = await session.scalar(select(Associe).where(Associe.nom == "Jessy"))
    if jessy is None:
        session.add(Associe(
            nom="Jessy",
            plafond_mensuel=5_000_000,
            versement_fixe_mensuel=3_000_000,
            versement_fixe_mois_debut_ordre=2,
            is_active=True,
        ))
        await session.flush()
        logger.info("Associée Jessy créée")

    # --- ADMIN (obligatoire) -----------------------------------------
    existing_admin = await session.scalar(
        select(User).where(User.username == settings.bootstrap_admin_username)
    )
    if existing_admin is None:
        session.add(User(
            username=settings.bootstrap_admin_username,
            email=settings.bootstrap_admin_email,
            password_hash=_ph.hash(settings.bootstrap_admin_password),
            full_name=settings.bootstrap_admin_fullname,
            role="ADMIN",
            is_active=True,
        ))
        await session.flush()
        logger.info("ADMIN %s créé", settings.bootstrap_admin_username)
    else:
        logger.info("ADMIN %s déjà présent", settings.bootstrap_admin_username)