"""Schémas charges (ledger immuable)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChargeCreate(BaseModel):
    mois_id: int | None = None
    charge_catalogue_id: int | None = None
    libelle: str = Field(min_length=1, max_length=200)
    categorie: str = Field(pattern="^(FIXE|VARIABLE|AUTRE)$")
    montant: int = Field(gt=0)
    date_operation: date | None = None
    date_a_completer: bool = False
    mode_paiement_id: int | None = None
    reference: str | None = Field(default=None, max_length=100)
    observation: str | None = None

    @model_validator(mode="after")
    def _dates(self):
        if self.date_a_completer and self.date_operation is not None:
            raise ValueError("date_operation doit être absente si date_a_completer=true")
        if not self.date_a_completer and self.date_operation is None:
            raise ValueError("date_operation obligatoire si date_a_completer=false")
        return self


class ChargeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    annee_scolaire_id: int
    mois_id: int
    charge_catalogue_id: int | None
    libelle: str
    categorie: str
    montant: int
    date_operation: date | None
    date_a_completer: bool
    mode_paiement_id: int | None
    reference: str | None
    observation: str | None
    parent_charge_id: int | None
    created_by: int
    created_at: datetime