"""Schémas d'import Excel."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImportLigneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sheet: str
    row_index: int
    entity_type: str | None
    entity_id: str | None
    created_at: datetime


class SheetStat(BaseModel):
    sheet: str
    total: int
    created: int
    skipped: int
    errors: int
    warnings: list[str]


class ImportReport(BaseModel):
    file_name: str
    dry_run: bool
    sheets: list[SheetStat]
    total_created: int
    total_skipped: int
    total_errors: int
    started_at: datetime
    finished_at: datetime