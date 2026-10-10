"""Endpoints import Excel."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.imports import ImportLigne
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.schemas.imports import ImportLigneRead, ImportReport
from app.services import importer

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/excel", response_model=ImportReport)
async def import_excel(
    file: UploadFile = File(...),
    dry_run: bool = Query(False),
    current: User = Depends(require_permission(Resource.PARAMETRES, Action.CREATE)),
    session: AsyncSession = Depends(get_session),
) -> ImportReport:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(400, "Fichier .xlsx attendu")
    content = await file.read()
    if not content:
        raise HTTPException(400, "Fichier vide")
    try:
        result = await importer.import_workbook(
            session,
            file_bytes=content,
            file_name=file.filename,
            created_by=current.id,
            dry_run=dry_run,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return ImportReport.model_validate(result)


@router.get("/lignes", response_model=list[ImportLigneRead])
async def list_import_lignes(
    sheet: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    _: User = Depends(require_permission(Resource.PARAMETRES, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> list[ImportLigneRead]:
    stmt = select(ImportLigne).order_by(ImportLigne.id.desc()).limit(limit)
    if sheet:
        stmt = stmt.where(ImportLigne.sheet == sheet)
    rows = (await session.scalars(stmt)).all()
    return [ImportLigneRead.model_validate(r) for r in rows]