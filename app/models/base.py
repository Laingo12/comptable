"""Base déclarative + mixins transverses (timestamp, version optimiste)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, text
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base déclarative commune à tous les modèles."""

    # Permet d'utiliser `metadata` dans Alembic sans autre configuration.
    __table_args__ = {"schema": None}


class Timestamped:
    """Ajoute created_at / updated_at (UTC, côté serveur)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )


class Versioned:
    """Ajoute une colonne `version` + verrouillage optimiste SQLAlchemy."""

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        default=0,
    )

    @declared_attr.directive
    def __mapper_args__(cls) -> dict[str, Any]:  # noqa: N805
        # `cls.__table__` est disponible après la construction de la table.
        return {"version_id_col": cls.__table__.c.version}