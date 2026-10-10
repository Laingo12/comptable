"""Marqueurs d'import — idempotence par hash de ligne."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ImportLigne(Base):
    __tablename__ = "import_lignes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    sheet: Mapped[str] = mapped_column(Text, nullable=False)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


Index("ix_import_sheet", ImportLigne.sheet)
Index("ix_import_created", ImportLigne.created_at)