"""Schémas associés."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssocieCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    plafond_mensuel: int | None = Field(default=None, ge=0)
    versement_fixe_mensuel: int | None = Field(default=None, ge=0)
    versement_fixe_mois_debut_ordre: int | None = Field(default=None, ge=1, le=99)
    is_active: bool = True


class AssocieUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=200)
    plafond_mensuel: int | None = Field(default=None, ge=0)
    versement_fixe_mensuel: int | None = Field(default=None, ge=0)
    versement_fixe_mois_debut_ordre: int | None = Field(default=None, ge=1, le=99)
    is_active: bool | None = None


class AssocieRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str
    plafond_mensuel: int | None
    versement_fixe_mensuel: int | None
    versement_fixe_mois_debut_ordre: int | None
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime