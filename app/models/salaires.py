"""Ledger des paiements de salaires — immuable en base."""

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
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PaiementSalaire(Base):
    __tablename__ = "paiements_salaires"
    __table_args__ = (
        CheckConstraint(
            "type_part IN ('AVANCE_70','SOLDE_30')",
            name="chk_psal_type_part",
        ),
        CheckConstraint(
            "(parent_paiement_salaire_id IS NULL AND montant > 0) OR "
            "(parent_paiement_salaire_id IS NOT NULL AND montant < 0)",
            name="chk_psalaires_signe",
        ),
        CheckConstraint(
            "(date_paiement IS NOT NULL AND date_a_completer = false) OR "
            "(date_paiement IS NULL     AND date_a_completer = true)",
            name="chk_psalaires_date",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    annee_scolaire_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("annees_scolaires.id", ondelete="RESTRICT"), nullable=False
    )
    employe_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employes.id"), nullable=False
    )
    salaire_mensuel_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("salaires_mensuels.id"), nullable=False
    )
    type_part: Mapped[str] = mapped_column(String(10), nullable=False)
    montant: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date_paiement: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_a_completer: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    mode_paiement_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("modes_paiement.id"), nullable=True
    )
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_paiement_salaire_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("paiements_salaires.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


Index("ix_psal_mois", PaiementSalaire.salaire_mensuel_id, PaiementSalaire.type_part)
Index("ix_psal_parent", PaiementSalaire.parent_paiement_salaire_id)
Index(
    "uq_psalaires_annulation",
    PaiementSalaire.parent_paiement_salaire_id,
    unique=True,
    postgresql_where=text("parent_paiement_salaire_id IS NOT NULL"),
)
Index(
    "ix_psal_a_completer",
    PaiementSalaire.date_a_completer,
    postgresql_where=text("date_a_completer"),
)