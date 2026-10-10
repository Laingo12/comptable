"""Ledger des encaissements (immuable en base)."""

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
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Paiement(Base):
    __tablename__ = "paiements"
    __table_args__ = (
        CheckConstraint(
            "(parent_paiement_id IS NULL AND montant > 0) OR "
            "(parent_paiement_id IS NOT NULL AND montant < 0)",
            name="chk_paiements_signe",
        ),
        CheckConstraint(
            "(date_paiement IS NOT NULL AND date_a_completer = false) OR "
            "(date_paiement IS NULL     AND date_a_completer = true)",
            name="chk_paiements_date",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    annee_scolaire_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("annees_scolaires.id", ondelete="RESTRICT"), nullable=False
    )
    inscription_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("inscriptions.id", ondelete="RESTRICT"), nullable=True
    )
    type_paiement_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("types_paiement.id"), nullable=False
    )
    mois_concerne_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("mois_scolaires.id"), nullable=True
    )
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
    parent_paiement_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("paiements.id", ondelete="RESTRICT"), nullable=True
    )
    motif_annulation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


Index("ix_paie_annee_date", Paiement.annee_scolaire_id, Paiement.date_paiement)
Index("ix_paie_inscr_mois", Paiement.inscription_id, Paiement.mois_concerne_id)
Index("ix_paie_type", Paiement.type_paiement_id)
Index("ix_paie_parent", Paiement.parent_paiement_id)
Index(
    "uq_paiements_annulation",
    Paiement.parent_paiement_id,
    unique=True,
    postgresql_where=text("parent_paiement_id IS NOT NULL"),
)
Index(
    "ix_paie_a_completer",
    Paiement.date_a_completer,
    postgresql_where=text("date_a_completer"),
)