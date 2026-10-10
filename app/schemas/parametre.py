"""Schémas paramètres versionnés par année scolaire."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ParametreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    annee_scolaire_id: int
    cle: str
    valeur: Any
    description: str | None
    version: int
    updated_by: int | None
    updated_at: datetime


class ParametreUpsert(BaseModel):
    cle: str = Field(min_length=1, max_length=100)
    valeur: Any
    description: str | None = None


class ParametresBulkUpsert(BaseModel):
    annee_scolaire_id: int
    parametres: list[ParametreUpsert]