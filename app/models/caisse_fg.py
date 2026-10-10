"""Caisse FG — sous-registre distinct, ledger immuable en base."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime,
    FetchedValue, ForeignKey, Index, SmallInteger, String, Text, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CaisseFgMouvement(Base):
    __tablename__ = "caisse_fg_mouvements"
    __table_args__ = (
        CheckConstraint("sens IN ('ENTREE','SORTIE')", name="chk_fg_sens"),
        CheckConstraint("montant > 0", name="chk_fg_montant"),
        CheckConstraint(
            "(date_operation IS NOT NULL AND date_a_completer = false) OR "
            "(date_operation IS NULL     AND date_a_completer = true)",
            name="chk_fg_date",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    annee_scolaire_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("annees_scolaires.id", ondelete="RESTRICT"),
        nullable=False, server_default=FetchedValue(),
    )
    mois_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("mois_scolaires.id"),
        nullable=False, server_default=FetchedValue(),
    )
    sens: Mapped[str] = mapped_column(String(6), nullable=False)
    montant: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date_operation: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_a_completer: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    remarque: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode_paiement_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("modes_paiement.id"), nullable=True
    )
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_mouvement_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("caisse_fg_mouvements.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


Index("ix_fg_annee_mois", CaisseFgMouvement.annee_scolaire_id, CaisseFgMouvement.mois_id)
Index("ix_fg_sens", CaisseFgMouvement.sens)
Index("ix_fg_parent", CaisseFgMouvement.parent_mouvement_id)
Index(
    "uq_fg_annulation",
    CaisseFgMouvement.parent_mouvement_id,
    unique=True,
    postgresql_where=text("parent_mouvement_id IS NOT NULL"),
)
Index(
    "ix_fg_a_completer",
    CaisseFgMouvement.date_a_completer,
    postgresql_where=text("date_a_completer"),
)