"""Associés dont la part peut être débitée par des prélèvements."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    SmallInteger,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, Versioned


class Associe(Base, Timestamped, Versioned):
    __tablename__ = "associes"
    __table_args__ = (
        CheckConstraint(
            "plafond_mensuel IS NULL OR plafond_mensuel >= 0",
            name="chk_associe_plafond",
        ),
        CheckConstraint(
            "versement_fixe_mensuel IS NULL OR versement_fixe_mensuel >= 0",
            name="chk_associe_vf",
        ),
        CheckConstraint(
            "versement_fixe_mois_debut_ordre IS NULL "
            "OR versement_fixe_mois_debut_ordre BETWEEN 1 AND 99",
            name="chk_associe_vf_ordre",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    plafond_mensuel: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    versement_fixe_mensuel: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    versement_fixe_mois_debut_ordre: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )