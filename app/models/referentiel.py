"""Référentiels : niveaux, mois scolaires, types et modes de paiement."""

from __future__ import annotations

from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Niveau(Base):
    __tablename__ = "niveaux"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    ordre: Mapped[int] = mapped_column(SmallInteger, nullable=False, unique=True)


class MoisScolaire(Base):
    __tablename__ = "mois_scolaires"
    __table_args__ = (
        CheckConstraint("ordre BETWEEN 1 AND 99", name="chk_mois_ordre"),
        CheckConstraint(
            "(est_scolaire = true AND date_debut IS NOT NULL AND date_fin IS NOT NULL "
            " AND date_limite_paiement IS NOT NULL) OR (est_scolaire = false)",
            name="chk_mois_dates",
        ),
        UniqueConstraint("annee_scolaire_id", "code", name="uq_mois_annee_code"),
        UniqueConstraint("annee_scolaire_id", "ordre", name="uq_mois_annee_ordre"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    annee_scolaire_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("annees_scolaires.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    ordre: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    date_debut: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_limite_paiement: Mapped[date | None] = mapped_column(Date, nullable=True)
    est_scolaire: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )


Index("ix_mois_scolaire", MoisScolaire.annee_scolaire_id, postgresql_where=text("est_scolaire"))


class TypePaiement(Base):
    __tablename__ = "types_paiement"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    ordre: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class ModePaiement(Base):
    __tablename__ = "modes_paiement"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    ordre: Mapped[int] = mapped_column(SmallInteger, nullable=False)