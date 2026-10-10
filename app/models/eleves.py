"""Familles, élèves (personne) et inscriptions (élève × année)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, Versioned


class Famille(Base, Timestamped, Versioned):
    __tablename__ = "familles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    contact_principal: Mapped[str | None] = mapped_column(Text, nullable=True)
    telephone: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    adresse: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


Index("ix_famille_tel", Famille.telephone)


class Eleve(Base, Timestamped, Versioned):
    """Personne physique, identifiée par un matricule stable à vie."""

    __tablename__ = "eleves"
    __table_args__ = (
        CheckConstraint("sexe IN ('M','F')", name="chk_eleve_sexe"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    matricule: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    prenoms: Mapped[str] = mapped_column(Text, nullable=False)
    sexe: Mapped[str | None] = mapped_column(String(1), nullable=True)
    date_naissance: Mapped[date | None] = mapped_column(Date, nullable=True)
    famille_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("familles.id", ondelete="SET NULL"),
        nullable=True,
    )


Index("ix_eleves_nom", Eleve.nom, Eleve.prenoms)
Index("ix_eleves_famille", Eleve.famille_id)


class Inscription(Base, Timestamped, Versioned):
    """Inscription d'un élève pour une année scolaire donnée."""

    __tablename__ = "inscriptions"
    __table_args__ = (
        UniqueConstraint("eleve_id", "annee_scolaire_id", name="uq_inscription_eleve_annee"),
        CheckConstraint("ecolage_mensuel >= 0", name="chk_inscr_eco"),
        CheckConstraint("remise_pct BETWEEN 0 AND 100", name="chk_inscr_remise"),
        CheckConstraint("droit_inscription_du >= 0", name="chk_inscr_droits"),
        CheckConstraint("frais_generaux_du >= 0", name="chk_inscr_fg"),
        CheckConstraint("statut IN ('ACTIF','SORTI')", name="chk_inscr_statut"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    eleve_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("eleves.id", ondelete="RESTRICT"),
        nullable=False,
    )
    annee_scolaire_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("annees_scolaires.id", ondelete="RESTRICT"),
        nullable=False,
    )
    niveau_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("niveaux.id"), nullable=False
    )
    mois_entree_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("mois_scolaires.id"), nullable=False
    )
    ecolage_mensuel: Mapped[int] = mapped_column(BigInteger, nullable=False)
    remise_pct: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    droit_inscription_du: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    frais_generaux_du: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    statut: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default=text("'ACTIF'")
    )
    date_sortie: Mapped[date | None] = mapped_column(Date, nullable=True)


Index("ix_inscr_annee_statut", Inscription.annee_scolaire_id, Inscription.statut)
Index("ix_inscr_niveau", Inscription.niveau_id)
Index("ix_inscr_mois_entree", Inscription.mois_entree_id)