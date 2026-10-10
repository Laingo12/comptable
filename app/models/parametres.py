"""Années scolaires, paramètres versionnés, grille tarifaire, catalogue de charges."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, Versioned


class AnneeScolaire(Base, Timestamped, Versioned):
    __tablename__ = "annees_scolaires"
    __table_args__ = (
        CheckConstraint("date_fin > date_debut", name="chk_annee_dates"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    libelle: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    date_debut: Mapped[date] = mapped_column(Date, nullable=False)
    date_fin: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )


Index(
    "uq_annee_active",
    AnneeScolaire.is_active,
    unique=True,
    postgresql_where=text("is_active"),
)


class Parametre(Base, Versioned):
    __tablename__ = "parametres"
    __table_args__ = (
        UniqueConstraint("annee_scolaire_id", "cle", name="uq_parametre"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    annee_scolaire_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("annees_scolaires.id", ondelete="CASCADE"),
        nullable=False,
    )
    cle: Mapped[str] = mapped_column(Text, nullable=False)
    valeur: Mapped[dict | list | str | int | bool] = mapped_column(JSONB, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )


class GrilleTarifaire(Base, Versioned):
    __tablename__ = "grille_tarifaire"
    __table_args__ = (
        UniqueConstraint("annee_scolaire_id", "niveau_id", name="uq_grille"),
        CheckConstraint("ecolage_mensuel >= 0", name="chk_grille_eco"),
        CheckConstraint("droit_inscription >= 0", name="chk_grille_inscr"),
        CheckConstraint("frais_generaux >= 0", name="chk_grille_fg"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    annee_scolaire_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("annees_scolaires.id", ondelete="CASCADE"),
        nullable=False,
    )
    niveau_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("niveaux.id"), nullable=False
    )
    ecolage_mensuel: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    droit_inscription: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    frais_generaux: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )


class ChargeCatalogue(Base, Versioned):
    __tablename__ = "charges_catalogue"
    __table_args__ = (
        CheckConstraint(
            "categorie IN ('FIXE','VARIABLE','AUTRE')",
            name="chk_charges_cat",
        ),
        CheckConstraint("montant_previsionnel >= 0", name="chk_charges_prev"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    annee_scolaire_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("annees_scolaires.id", ondelete="CASCADE"),
        nullable=True,
    )
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    categorie: Mapped[str] = mapped_column(String(10), nullable=False)
    montant_previsionnel: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )


Index("ix_charges_cat", ChargeCatalogue.annee_scolaire_id, ChargeCatalogue.categorie)
Index(
    "ix_charges_active",
    ChargeCatalogue.is_active,
    postgresql_where=text("is_active"),
)