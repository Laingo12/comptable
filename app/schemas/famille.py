"""Schémas familles."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FamilleCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    contact_principal: str | None = Field(default=None, max_length=200)
    telephone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    adresse: str | None = None
    notes: str | None = None


class FamilleUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=200)
    contact_principal: str | None = Field(default=None, max_length=200)
    telephone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    adresse: str | None = None
    notes: str | None = None


class FamilleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str
    contact_principal: str | None
    telephone: str | None
    email: str | None
    adresse: str | None
    notes: str | None
    version: int
    created_at: datetime
    updated_at: datetime