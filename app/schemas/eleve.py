"""Schémas élèves (personne) et inscriptions (élève × année)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EleveCreate(BaseModel):
    matricule: str | None = Field(default=None, max_length=50)
    nom: str = Field(min_length=1, max_length=200)
    prenoms: str = Field(min_length=1, max_length=200)
    sexe: str | None = Field(default=None, pattern="^[MF]$")
    date_naissance: date | None = None
    famille_id: int | None = None


class EleveUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=200)
    prenoms: str | None = Field(default=None, min_length=1, max_length=200)
    sexe: str | None = Field(default=None, pattern="^[MF]$")
    date_naissance: date | None = None
    famille_id: int | None = None


class EleveRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    matricule: str
    nom: str
    prenoms: str
    sexe: str | None
    date_naissance: date | None
    famille_id: int | None
    version: int
    created_at: datetime
    updated_at: datetime


class InscriptionCreate(BaseModel):
    eleve_id: int
    niveau_id: int
    mois_entree_id: int
    ecolage_mensuel: int | None = Field(default=None, ge=0)
    remise_pct: int | None = Field(default=None, ge=0, le=100)
    droit_inscription_du: int | None = Field(default=None, ge=0)
    frais_generaux_du: int | None = Field(default=None, ge=0)


class InscriptionUpdate(BaseModel):
    niveau_id: int | None = None
    mois_entree_id: int | None = None
    ecolage_mensuel: int | None = Field(default=None, ge=0)
    remise_pct: int | None = Field(default=None, ge=0, le=100)
    droit_inscription_du: int | None = Field(default=None, ge=0)
    frais_generaux_du: int | None = Field(default=None, ge=0)
    statut: str | None = Field(default=None, pattern="^(ACTIF|SORTI)$")
    date_sortie: date | None = None


class InscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    eleve_id: int
    annee_scolaire_id: int
    niveau_id: int
    mois_entree_id: int
    ecolage_mensuel: int
    remise_pct: int
    droit_inscription_du: int
    frais_generaux_du: int
    statut: str
    date_sortie: date | None
    version: int
    created_at: datetime
    updated_at: datetime