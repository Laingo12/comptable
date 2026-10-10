"""Schémas situation écolage et fiche élève."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class PaiementLigne(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    montant: int
    date_paiement: date | None
    mode_paiement_id: int | None
    reference: str | None
    qualificatif: str  # "NORMAL" | "AVANCE" | "RETARD"


class MoisSituation(BaseModel):
    mois_id: int
    code: str
    libelle: str
    ordre: int
    date_limite_paiement: date | None
    du: int
    paye: int
    reste_du: int
    statut: str           # PAYE | PARTIEL | IMPAYE
    echu: bool
    en_retard: bool
    paiements: list[PaiementLigne]


class SituationSimple(BaseModel):
    du: int
    paye: int
    reste_du: int
    statut: str


class TotauxSituation(BaseModel):
    du: int
    paye: int
    reste_du: int
    taux_recouvrement: float  # 0..100


class EleveSituation(BaseModel):
    eleve_id: int
    inscription_id: int
    annee_scolaire_id: int
    matricule: str
    nom: str
    prenoms: str
    niveau_id: int
    mois_entree_id: int
    ecolage_mensuel: int
    remise_pct: int
    droits_inscription: SituationSimple
    frais_generaux: SituationSimple
    mois: list[MoisSituation]
    totaux: TotauxSituation