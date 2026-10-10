"""Les 5 ledgers + audit_log : UPDATE/DELETE refusés par grant, TRUNCATE par trigger."""

from __future__ import annotations

import pytest
from sqlalchemy import text

LEDGERS = (
    "paiements",
    "charges",
    "paiements_salaires",
    "prelevements",
    "caisse_fg_mouvements",
    "audit_log",
)


@pytest.mark.asyncio
@pytest.mark.parametrize("table", LEDGERS)
async def test_update_refuse_au_niveau_grant(session_app, table):
    with pytest.raises(Exception) as exc:
        await session_app.execute(text(f"UPDATE {table} SET id = id"))
    assert "refusé" in str(exc.value).lower() or "denied" in str(exc.value).lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("table", LEDGERS)
async def test_delete_refuse_au_niveau_grant(session_app, table):
    with pytest.raises(Exception) as exc:
        await session_app.execute(text(f"DELETE FROM {table}"))
    assert "refusé" in str(exc.value).lower() or "denied" in str(exc.value).lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("table", LEDGERS)
async def test_truncate_refuse_par_trigger(session_owner, table):
    with pytest.raises(Exception) as exc:
        await session_owner.execute(text(f"TRUNCATE {table}"))
    assert "interdit" in str(exc.value).lower()