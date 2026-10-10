"""Import Excel : idempotence, lignes non datées, hors année, rapport."""

from __future__ import annotations

import io
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from openpyxl import Workbook
from sqlalchemy import select

from app.core.security import hash_password
from app.main import app
from app.models.audit import AuditLog
from app.models.paiements import Paiement
from app.models.prelevements import Prelevement


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(session_owner):
    suffix = uuid.uuid4().hex[:8]
    from app.models.user import User as U
    session_owner.add(U(
        username=f"imp_{suffix}", email=None,
        password_hash=hash_password("imp12345"),
        full_name=f"Imp {suffix}", role="ADMIN", is_active=True,
    ))
    await session_owner.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/login",
                          json={"username": f"imp_{suffix}", "password": "imp12345"})
        return r.json()["access_token"]


async def _create_eleve(client, headers, suffix: str):
    r = await client.post("/api/v1/familles",
                          json={"nom": f"ImpFam {suffix}"}, headers=headers)
    famille_id = r.json()["id"]
    r2 = await client.post("/api/v1/eleves",
                           json={"nom": f"Eleve{suffix}", "prenoms": "Test",
                                 "famille_id": famille_id}, headers=headers)
    eleve = r2.json()
    r3 = await client.get("/api/v1/niveaux", headers=headers)
    ps = next(n for n in r3.json() if n["code"] == "PS")
    r4 = await client.get("/api/v1/mois-scolaires", headers=headers)
    m09 = next(m for m in r4.json() if m["code"] == "2026-09")
    await client.post(
        "/api/v1/inscriptions",
        json={"eleve_id": eleve["id"], "niveau_id": ps["id"], "mois_entree_id": m09["id"]},
        headers=headers,
    )
    return eleve["matricule"]


def _make_workbook(rows_suivi, rows_retraits=None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "SUIVI ECOLAGES"
    ws.append(["Matricule", "Mois", "Montant", "Date", "Mode", "Référence"])
    for r in rows_suivi:
        ws.append(r)
    if rows_retraits:
        ws2 = wb.create_sheet("RETRAITS JESSY")
        ws2.append(["Montant", "Date", "Destinataire", "Motif"])
        for r in rows_retraits:
            ws2.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_import_suivi_ecolages_et_idempotence(client, admin_token, session_app):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]
    matricule = await _create_eleve(client, headers, suffix)

    # 2 lignes : une datée (normal), une non datée (NON_DATE)
    content = _make_workbook([
        [matricule, "2026-09", 100_000, "2026-09-05", "Espèces", f"REC-{suffix}"],
        [matricule, "2026-10", 100_000, None, "MVola", f"REC2-{suffix}"],
    ])
    files = {"file": ("test.xlsx", content,
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = await client.post("/api/v1/import/excel", files=files, headers=headers)
    assert r.status_code == 200, r.text
    rep = r.json()
    assert rep["dry_run"] is False
    suivi = next(s for s in rep["sheets"] if s["sheet"] == "SUIVI ECOLAGES")
    assert suivi["created"] == 2
    assert suivi["errors"] == 0

    # Vérifier en base
    rows = (await session_app.scalars(
        select(Paiement).where(Paiement.inscription_id.is_not(None))
    )).all()
    created = [p for p in rows if p.reference in (f"REC-{suffix}", f"REC2-{suffix}")]
    assert len(created) == 2
    non_date = next(p for p in created if p.reference == f"REC2-{suffix}")
    assert non_date.date_a_completer is True
    assert non_date.mois_concerne_id is not None  # rempli par la colonne mois

    # Deuxième import : tout doit être skippé
    files2 = {"file": ("test.xlsx", content,
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r2 = await client.post("/api/v1/import/excel", files=files2, headers=headers)
    assert r2.status_code == 200
    rep2 = r2.json()
    suivi2 = next(s for s in rep2["sheets"] if s["sheet"] == "SUIVI ECOLAGES")
    assert suivi2["created"] == 0
    assert suivi2["skipped"] == 2


@pytest.mark.asyncio
async def test_import_dry_run(client, admin_token, session_app):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]
    matricule = await _create_eleve(client, headers, suffix)

    content = _make_workbook([
        [matricule, "2026-09", 100_000, "2026-09-05", "Espèces", f"DRY-{suffix}"],
    ])
    files = {"file": ("test.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = await client.post("/api/v1/import/excel?dry_run=true", files=files, headers=headers)
    assert r.status_code == 200
    rep = r.json()
    assert rep["dry_run"] is True
    suivi = next(s for s in rep["sheets"] if s["sheet"] == "SUIVI ECOLAGES")
    assert suivi["created"] == 1

    # Rien ne doit être en base
    row = await session_app.scalar(
        select(Paiement).where(Paiement.reference == f"DRY-{suffix}")
    )
    assert row is None


@pytest.mark.asyncio
async def test_import_prelevements_dates_hors_annee(client, admin_token, session_app):
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]

    content = _make_workbook(
        rows_suivi=[],
        rows_retraits=[
            [50_000, "2027-08-15", "FOURNITURES LUCKAS", f"Hors-annee {suffix}"],
        ],
    )
    files = {"file": ("test.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = await client.post("/api/v1/import/excel", files=files, headers=headers)
    assert r.status_code == 200, r.text
    rep = r.json()
    ret = next(s for s in rep["sheets"] if s["sheet"] == "RETRAITS JESSY")
    assert ret["created"] == 1

    # Le trigger DB doit avoir positionné mois_id sur HORS_ANNEE
    from app.models.referentiel import MoisScolaire
    hors = await session_app.scalar(
        select(MoisScolaire).where(MoisScolaire.code == "HORS_ANNEE")
    )
    pr = await session_app.scalar(
        select(Prelevement).where(Prelevement.motif.is_not(None))
        .order_by(Prelevement.id.desc()).limit(1)
    )
    assert pr is not None
    assert pr.mois_id == hors.id


@pytest.mark.asyncio
async def test_import_audit_trail(client, admin_token, session_app):
    """Chaque ligne importée doit produire une entrée audit_log."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6]
    matricule = await _create_eleve(client, headers, suffix)

    content = _make_workbook([
        [matricule, "2026-11", 80_000, "2026-11-03", None, f"AUDIT-{suffix}"],
    ])
    files = {"file": ("test.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = await client.post("/api/v1/import/excel", files=files, headers=headers)
    assert r.status_code == 200

    rows = (await session_app.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "paiements",
            AuditLog.action == "INSERT",
        ).order_by(AuditLog.id.desc()).limit(5)
    )).all()
    # Au moins une ligne correspondant au paiement créé
    found = False
    for row in rows:
        if row.after_state and row.after_state.get("reference") == f"AUDIT-{suffix}":
            found = True
            break
    assert found