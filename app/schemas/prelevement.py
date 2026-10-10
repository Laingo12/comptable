"""Schémas prélèvements (ledger immuable)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PrelevementCreate(BaseModel):
    associe_id: int
    type: str = Field(pattern="^(RETRAIT|VERSEMENT_FIXE|SUPPLEMENT)$")
    montant: int = Field(gt=0)
    date_prelevement: date | None = None
    date_a_completer: bool = False
    destinataire: str | None = Field(default=None, max_length=200)
    motif: str | None = None
    mode_paiement_id: int | None = None
    reference: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def _dates(self):
        if self.date_a_completer and self.date_prelevement is not None:
            raise ValueError("date_prelevement doit être absente si date_a_completer=true")
        if not self.date_a_completer and self.date_prelevement is None:
            raise ValueError("date_prelevement obligatoire si date_a_completer=false")
        return self


class PrelevementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    annee_scolaire_id: int
    associe_id: int
    mois_id: int
    type: str
    montant: int
    date_prelevement: date | None
    date_a_completer: bool
    destinataire: str | None
    motif: str | None
    mode_paiement_id: int | None
    reference: str | None
    parent_prelevement_id: int | None
    created_by: int
    created_at: datetime