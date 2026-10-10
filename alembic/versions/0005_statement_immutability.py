"""add statement-level triggers for immutability

Revision ID: 0005_stmt_immutability
Revises: 0004_refresh_family
Create Date: 2026-10-09
"""
from __future__ import annotations

from alembic import op

revision = "0005_stmt_immutability"
down_revision = "0004_refresh_family"
branch_labels = None
depends_on = None

LEDGERS = (
    "paiements",
    "charges",
    "paiements_salaires",
    "prelevements",
    "caisse_fg_mouvements",
    "audit_log",
)


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION forbid_mutation_stmt() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'Ledger immuable : % interdit sur % (statement)',
            TG_OP, TG_TABLE_NAME
            USING ERRCODE = 'restrict_violation';
        END;
        $$ LANGUAGE plpgsql;
    """)
    for table in LEDGERS:
        op.execute(
            f"CREATE TRIGGER trg_{table}_immutable_stmt "
            f"BEFORE UPDATE OR DELETE ON {table} "
            f"FOR EACH STATEMENT EXECUTE FUNCTION forbid_mutation_stmt();"
        )


def downgrade() -> None:
    for table in LEDGERS:
        op.execute(
            f"DROP TRIGGER IF EXISTS trg_{table}_immutable_stmt ON {table};"
        )
    op.execute("DROP FUNCTION IF EXISTS forbid_mutation_stmt();")