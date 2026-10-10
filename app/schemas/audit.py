"""Schémas d'audit (lecture seule)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None
    before_state: dict | None
    after_state: dict | None
    ip: str | None
    user_agent: str | None
    created_at: datetime


class AuditPage(BaseModel):
    items: list[AuditLogRead]
    total: int
    page: int
    page_size: int