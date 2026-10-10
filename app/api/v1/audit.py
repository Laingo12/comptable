"""GET /api/v1/audit — ADMIN, paginé et filtrable."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.audit import AuditLog
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.schemas.audit import AuditLogRead, AuditPage

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditPage)
async def list_audit(
    _: User = Depends(require_permission(Resource.AUDIT_LOG, Action.READ)),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str | None = Query(None),
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    user_id: int | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
) -> AuditPage:
    conditions = []
    if action:
        conditions.append(AuditLog.action == action)
    if entity_type:
        conditions.append(AuditLog.entity_type == entity_type)
    if entity_id:
        conditions.append(AuditLog.entity_id == entity_id)
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if date_from:
        conditions.append(AuditLog.created_at >= date_from)
    if date_to:
        conditions.append(AuditLog.created_at <= date_to)

    base = select(AuditLog)
    counter = select(func.count(AuditLog.id))
    for c in conditions:
        base = base.where(c)
        counter = counter.where(c)

    total = (await session.execute(counter)).scalar_one()
    rows = (
        await session.execute(
            base.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return AuditPage(
        items=[AuditLogRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )