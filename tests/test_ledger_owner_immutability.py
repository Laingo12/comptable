"""UPDATE/DELETE en tant que smartkids_owner : refusés par forbid_mutation."""

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


@pytest.mark.parametrize("table", LEDGERS)
async def test_owner_update_refused_by_trigger(session_owner, table):
    with pytest.raises(Exception) as exc:
        await session_owner.execute(text(f"UPDATE {table} SET id = id"))
    assert "interdit" in str(exc.value).lower()


@pytest.mark.parametrize("table", LEDGERS)
async def test_owner_delete_refused_by_trigger(session_owner, table):
    with pytest.raises(Exception) as exc:
        await session_owner.execute(text(f"DELETE FROM {table}"))
    assert "interdit" in str(exc.value).lower()