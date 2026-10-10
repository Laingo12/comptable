"""Schémas paiements."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PaiementCreate(BaseModel):
    inscription_id: int | None = None
    type_paiement_id: int
    mois_concerne_id: int | None = None
    montant: int = Field(gt=0)
    date_paiement: date | None = None
    date_a_completer: bool = False
    mode_paiement_id: int | None = None
    reference: str | None = Field(default=None, max_length=100)
    observation: str | None = None

    @model_validator(mode="after")
    def _check_dates(self):
        if self.date_a_completer and self.date_paiement is not None:
            raise ValueError("date_paiement doit être absente si date_a_completer=true")
        if not self.date_a_completer and self.date_paiement is None:
            raise ValueError("date_paiement obligatoire si date_a_completer=false")
        return self


class AnnulationRequest(BaseModel):
    motif: str = Field(min_length=1, max_length=500)


class PaiementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    annee_scolaire_id: int
    inscription_id: int | None
    type_paiement_id: int
    mois_concerne_id: int | None
    montant: int
    date_paiement: date | None
    date_a_completer: bool
    mode_paiement_id: int | None
    reference: str | None
    observation: str | None
    parent_paiement_id: int | None
    motif_annulation: str | None
    created_by: int
    created_at: datetime