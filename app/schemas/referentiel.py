"""Schémas référentiels : niveaux, mois scolaires, types et modes de paiement."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class NiveauRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    libelle: str
    ordre: int


class MoisScolaireRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    annee_scolaire_id: int
    code: str
    libelle: str
    ordre: int
    date_debut: date | None
    date_fin: date | None
    date_limite_paiement: date | None
    est_scolaire: bool


class TypePaiementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    libelle: str
    ordre: int


class ModePaiementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    libelle: str
    ordre: int


class AnneeScolaireRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    libelle: str
    date_debut: date
    date_fin: date
    is_active: bool
    version: int


class GrilleTarifaireRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    annee_scolaire_id: int
    niveau_id: int
    ecolage_mensuel: int
    droit_inscription: int
    frais_generaux: int
    version: int


class GrilleTarifaireUpsert(BaseModel):
    niveau_id: int
    ecolage_mensuel: int = Field(ge=0)
    droit_inscription: int = Field(ge=0)
    frais_generaux: int = Field(ge=0)


class ChargeCatalogueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    annee_scolaire_id: int | None
    code: str | None
    libelle: str
    categorie: str
    montant_previsionnel: int
    is_active: bool
    version: int


class ChargeCatalogueCreate(BaseModel):
    annee_scolaire_id: int | None = None
    code: str | None = Field(default=None, max_length=50)
    libelle: str = Field(min_length=1, max_length=200)
    categorie: str = Field(pattern="^(FIXE|VARIABLE|AUTRE)$")
    montant_previsionnel: int = Field(default=0, ge=0)


class ChargeCatalogueUpdate(BaseModel):
    libelle: str | None = Field(default=None, min_length=1, max_length=200)
    categorie: str | None = Field(default=None, pattern="^(FIXE|VARIABLE|AUTRE)$")
    montant_previsionnel: int | None = Field(default=None, ge=0)
    is_active: bool | None = None