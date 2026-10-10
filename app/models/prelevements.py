from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime,
    FetchedValue, ForeignKey, Index, SmallInteger, String, Text, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Prelevement(Base):
    __tablename__ = "prelevements"
    __table_args__ = (
        CheckConstraint(
            "type IN ('RETRAIT','VERSEMENT_FIXE','SUPPLEMENT')",
            name="chk_prel_type",
        ),
        CheckConstraint(
            "(parent_prelevement_id IS NULL AND montant > 0) OR "
            "(parent_prelevement_id IS NOT NULL AND montant < 0)",
            name="chk_prel_signe",
        ),
        CheckConstraint(
            "(date_prelevement IS NOT NULL AND date_a_completer = false) OR "
            "(date_prelevement IS NULL     AND date_a_completer = true)",
            name="chk_prel_date",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # FetchedValue : remplis par le trigger derive_prelevement(),
    # donc à récupérer via RETURNING après INSERT.
    annee_scolaire_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("annees_scolaires.id", ondelete="RESTRICT"),
        nullable=False,
        server_default=FetchedValue(),
    )
    associe_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("associes.id", ondelete="RESTRICT"), nullable=False
    )
    mois_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("mois_scolaires.id"),
        nullable=False,
        server_default=FetchedValue(),
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'RETRAIT'")
    )
    montant: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date_prelevement: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_a_completer: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    destinataire: Mapped[str | None] = mapped_column(Text, nullable=True)
    motif: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode_paiement_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("modes_paiement.id"), nullable=True
    )
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_prelevement_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("prelevements.id", ondelete="RESTRICT"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


Index("ix_prel_annee_mois", Prelevement.annee_scolaire_id, Prelevement.mois_id)
Index("ix_prel_associe", Prelevement.associe_id)
Index("ix_prel_parent", Prelevement.parent_prelevement_id)
Index(
    "uq_prelevements_annulation",
    Prelevement.parent_prelevement_id,
    unique=True,
    postgresql_where=text("parent_prelevement_id IS NOT NULL"),
)
Index(
    "ix_prel_a_completer",
    Prelevement.date_a_completer,
    postgresql_where=text("date_a_completer"),
)