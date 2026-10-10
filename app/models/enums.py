"""Énumérations métier (str) utilisées dans les CHECK et côté application."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "ADMIN"
    COMPTABLE = "COMPTABLE"
    SAISIE = "SAISIE"
    CAISSE_FG = "CAISSE_FG"
    LECTURE = "LECTURE"


class AuditAction(StrEnum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ANNULATION = "ANNULATION"
    EXPORT = "EXPORT"


class NiveauCode(StrEnum):
    CRECHE = "CRECHE"
    TPS = "TPS"
    PS = "PS"
    MS = "MS"
    GS = "GS"
    CP = "CP"
    CE1 = "CE1"
    CE2 = "CE2"
    CM1 = "CM1"
    CM2 = "CM2"


class TypePaiementCode(StrEnum):
    ECOLAGE = "ECOLAGE"
    INSCRIPTION = "INSCRIPTION"
    FRAIS_GENERAUX = "FRAIS_GENERAUX"
    AUTRE = "AUTRE"


class ModePaiementCode(StrEnum):
    ESPECES = "ESPECES"
    MVOLA = "MVOLA"
    CHEQUE = "CHEQUE"
    VIREMENT = "VIREMENT"
    NON_PRECISE = "NON_PRECISE"


class ChargeCategorie(StrEnum):
    FIXE = "FIXE"
    VARIABLE = "VARIABLE"
    AUTRE = "AUTRE"


class InscriptionStatut(StrEnum):
    ACTIF = "ACTIF"
    SORTI = "SORTI"


class EmployeStatut(StrEnum):
    ACTIF = "ACTIF"
    SORTI = "SORTI"


class PartSalaire(StrEnum):
    AVANCE_70 = "AVANCE_70"
    SOLDE_30 = "SOLDE_30"


class SensCaisseFg(StrEnum):
    ENTREE = "ENTREE"
    SORTIE = "SORTIE"


class TypePrelevement(StrEnum):
    RETRAIT = "RETRAIT"
    VERSEMENT_FIXE = "VERSEMENT_FIXE"
    SUPPLEMENT = "SUPPLEMENT"