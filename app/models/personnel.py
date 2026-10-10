"""Employés et salaires mensuels contractualisés."""

from __future__ import annotations

from datetime import date

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, Versioned


class Employe(Base, Timestamped, Versioned):
    __tablename__ = "employes"
    __table_args__ = (
        CheckConstraint("salaire_mensuel >= 0", name="chk_employe_salaire"),
        CheckConstraint("statut IN ('ACTIF','SORTI')", name="chk_employe_statut"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    prenom: Mapped[str] = mapped_column(Text, nullable=False)
    poste: Mapped[str | None] = mapped_column(Text, nullable=True)
    salaire_mensuel: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    date_embauche: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_sortie: Mapped[date | None] = mapped_column(Date, nullable=True)
    statut: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default=text("'ACTIF'")
    )


class SalaireMensuel(Base):
    __tablename__ = "salaires_mensuels"
    __table_args__ = (
        UniqueConstraint("employe_id", "mois_id", name="uq_salaire_mensuel"),
        CheckConstraint("montant_brut >= 0", name="chk_sal_brut"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    employe_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("employes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    annee_scolaire_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("annees_scolaires.id"), nullable=False
    )
    mois_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("mois_scolaires.id"), nullable=False
    )
    montant_brut: Mapped[int] = mapped_column(BigInteger, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


Index("ix_sal_mois", SalaireMensuel.mois_id)
Index("ix_sal_employe", SalaireMensuel.employe_id)