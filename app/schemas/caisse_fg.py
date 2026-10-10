"""Schémas caisse FG (ledger immuable)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaisseFgCreate(BaseModel):
    sens: str = Field(pattern="^(ENTREE|SORTIE)$")
    montant: int = Field(gt=0)
    libelle: str = Field(min_length=1, max_length=200)
    date_operation: date | None = None
    date_a_completer: bool = False
    remarque: str | None = None
    mode_paiement_id: int | None = None
    reference: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def _dates(self):
        if self.date_a_completer and self.date_operation is not None:
            raise ValueError("date_operation doit être absente si date_a_completer=true")
        if not self.date_a_completer and self.date_operation is None:
            raise ValueError("date_operation obligatoire si date_a_completer=false")
        return self


class CaisseFgRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    annee_scolaire_id: int
    mois_id: int
    sens: str
    montant: int
    date_operation: date | None
    date_a_completer: bool
    libelle: str
    remarque: str | None
    mode_paiement_id: int | None
    reference: str | None
    parent_mouvement_id: int | None
    created_by: int
    created_at: datetime