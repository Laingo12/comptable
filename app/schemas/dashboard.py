"""Schémas dashboards mensuel et annuel."""

from __future__ import annotations

from pydantic import BaseModel


class EncaissementParMode(BaseModel):
    mode_paiement_id: int | None
    mode_code: str | None
    total: int


class EncaissementParType(BaseModel):
    type_paiement_id: int
    type_code: str
    total: int


class EncaissementJour(BaseModel):
    jour: int
    total: int
    cumul: int


class SituationCompteurs(BaseModel):
    payes: int
    partiels: int
    impayes: int
    en_retard: int


class SalairesInfo(BaseModel):
    brut_total: int
    du_70: int
    du_30: int
    paye_70: int
    paye_30: int
    disponible_pour_70: int
    pct_payable_25: float
    somme_manquante_25: int


class ComparatifLigne(BaseModel):
    libelle: str
    reel: int
    previsionnel: int
    ecart: int


class DashboardMensuel(BaseModel):
    annee_scolaire_id: int
    mois_id: int
    mois_code: str
    mois_libelle: str
    ordre: int

    # CA
    ca_ecolage: int
    ca_inscription: int
    ca_frais_generaux: int
    ca_autre: int
    ca_total_brut: int
    ca_retenu: int

    # Avances / retards du mois (information)
    avances: int
    retards_regularises: int

    # Détails
    par_mode: list[EncaissementParMode]
    par_type: list[EncaissementParType]
    par_jour: list[EncaissementJour]

    # Écolage
    ecolage_attendu: int
    ecolage_recu: int
    ecolage_reste_du: int
    taux_recouvrement: float
    compteurs: SituationCompteurs

    # Charges et résultat
    charges: int
    salaires: int
    resultat_avant_prelevements: int
    prelevements_mois: int
    resultat_apres_prelevements: int

    # Trésorerie
    tresorerie_debut: int
    tresorerie_fin: int

    # Priorité Jessy (10) puis salaires (25)
    jessy_prioritaire_10: int
    salaires: SalairesInfo

    # Comparatif réel vs prévisionnel
    comparatif: list[ComparatifLigne]


class MoisAnneeResume(BaseModel):
    mois_code: str
    mois_libelle: str
    ordre: int
    ca_retenu: int
    charges: int
    salaires: int
    prelevements: int
    resultat_apres_prelevements: int
    tresorerie_fin: int


class DashboardAnnuel(BaseModel):
    annee_scolaire_id: int
    libelle: str
    effectif: int
    ca_ecolage: int
    ca_inscription: int
    ca_frais_generaux: int
    ca_autre: int
    ca_total_brut: int
    ca_retenu: int
    verse_associes: int
    retards_a_recouvrer: int
    avances_percues: int
    fg_restants_dus: int
    droits_inscription_restants_dus: int
    tresorerie_actuelle: int
    somme_manquante_cumulee: int
    mois: list[MoisAnneeResume]