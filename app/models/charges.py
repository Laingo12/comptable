"""Ledger des décaissements (charges) — immuable en base."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime,
    FetchedValue, ForeignKey, Index, SmallInteger, String, Text, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Charge(Base):
    __tablename__ = "charges"
    __table_args__ = (
        CheckConstraint(
            "categorie IN ('FIXE','VARIABLE','AUTRE')",
            name="chk_charges_categorie",
        ),
        CheckConstraint(
            "(parent_charge_id IS NULL AND montant > 0) OR "
            "(parent_charge_id IS NOT NULL AND montant < 0)",
            name="chk_charges_signe",
        ),
        CheckConstraint(
            "(date_operation IS NOT NULL AND date_a_completer = false) OR "
            "(date_operation IS NULL     AND date_a_completer = true)",
            name="chk_charges_date",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    annee_scolaire_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("annees_scolaires.id", ondelete="RESTRICT"), nullable=False
    )
    mois_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("mois_scolaires.id"),
        nullable=False,
        server_default=FetchedValue(),
    )
    charge_catalogue_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("charges_catalogue.id"), nullable=True
    )
    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    categorie: Mapped[str] = mapped_column(String(10), nullable=False)
    montant: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date_operation: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_a_completer: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    mode_paiement_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("modes_paiement.id"), nullable=True
    )
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_charge_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("charges.id", ondelete="RESTRICT"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


Index("ix_chg_annee_mois", Charge.annee_scolaire_id, Charge.mois_id)
Index("ix_chg_cat", Charge.categorie)
Index("ix_chg_parent", Charge.parent_charge_id)
Index(
    "uq_charges_annulation",
    Charge.parent_charge_id,
    unique=True,
    postgresql_where=text("parent_charge_id IS NOT NULL"),
)
Index(
    "ix_chg_a_completer",
    Charge.date_a_completer,
    postgresql_where=text("date_a_completer"),
)