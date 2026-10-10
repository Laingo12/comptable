"""Schémas salaires mensuels et paiements de salaires."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SalaireMensuelCreate(BaseModel):
    employe_id: int
    mois_id: int
    montant_brut: int = Field(gt=0)
    notes: str | None = None


class SalaireMensuelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employe_id: int
    annee_scolaire_id: int
    mois_id: int
    montant_brut: int
    notes: str | None


class SalaireMensuelGenerer(BaseModel):
    mois_id: int
    annee_scolaire_id: int | None = None
    montant_brut_par_defaut: int | None = Field(default=None, ge=0)


class PaiementSalaireCreate(BaseModel):
    salaire_mensuel_id: int
    type_part: str = Field(pattern="^(AVANCE_70|SOLDE_30)$")
    montant: int = Field(gt=0)
    date_paiement: date | None = None
    date_a_completer: bool = False
    mode_paiement_id: int | None = None
    reference: str | None = Field(default=None, max_length=100)
    observation: str | None = None

    @model_validator(mode="after")
    def _dates(self):
        if self.date_a_completer and self.date_paiement is not None:
            raise ValueError("date_paiement doit être absente si date_a_completer=true")
        if not self.date_a_completer and self.date_paiement is None:
            raise ValueError("date_paiement obligatoire si date_a_completer=false")
        return self


class PaiementSalaireRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    annee_scolaire_id: int
    employe_id: int
    salaire_mensuel_id: int
    type_part: str
    montant: int
    date_paiement: date | None
    date_a_completer: bool
    mode_paiement_id: int | None
    reference: str | None
    observation: str | None
    parent_paiement_salaire_id: int | None
    created_by: int
    created_at: datetime