"""Endpoints d'export (Excel, reçus)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.models.enums import AuditAction
from app.models.user import User
from app.permissions.rbac import Action, Resource
from app.services import exports as svc

router = APIRouter(prefix="/exports", tags=["exports"])

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type=_XLSX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/dashboard-annuel.xlsx")
async def export_dashboard_annuel(
    annee_scolaire_id: int | None = Query(None),
    _: User = Depends(require_permission(Resource.EXPORTS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        content = await svc.export_dashboard_annuel_excel(
            session, annee_id=annee_scolaire_id,
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return _xlsx_response(content, "dashboard_annuel.xlsx")


@router.get("/eleves/{eleve_id}/situation.xlsx")
async def export_situation_eleve(
    eleve_id: int,
    annee_scolaire_id: int | None = Query(None),
    _: User = Depends(require_permission(Resource.EXPORTS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        content = await svc.export_situation_eleve_excel(
            session, eleve_id=eleve_id, annee_id=annee_scolaire_id,
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return _xlsx_response(content, f"situation_eleve_{eleve_id}.xlsx")


@router.get("/paiements.xlsx")
async def export_paiements(
    annee_scolaire_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    _: User = Depends(require_permission(Resource.EXPORTS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        content = await svc.export_paiements_excel(
            session, annee_id=annee_scolaire_id,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return _xlsx_response(content, "paiements.xlsx")


@router.get("/paiements/{paiement_id}/recu")
async def receipt(
    paiement_id: int,
    format: str = Query("pdf", pattern="^(pdf|html)$"),
    _: User = Depends(require_permission(Resource.EXPORTS, Action.READ)),
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        payload = await svc.receipt_payload(session, paiement_id=paiement_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))

    html = svc.render_receipt_html(payload)

    if format == "html":
        return Response(content=html, media_type="text/html; charset=utf-8")

    pdf = svc.try_pdf(html)
    if pdf is None:
        # WeasyPrint indisponible (typiquement : GTK manquant sur Windows dev).
        # On renvoie l'HTML pour ne pas casser le client.
        return Response(
            content=html,
            media_type="text/html; charset=utf-8",
            headers={"X-Receipt-Fallback": "html-weasyprint-unavailable"},
        )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="recu_{paiement_id}.pdf"'},
    )