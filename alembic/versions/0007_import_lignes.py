"""create import_lignes table for idempotent imports

Revision ID: 0007_import_lignes
Revises: 0006_drop_psalaire_derive
Create Date: 2026-10-10
"""
from __future__ import annotations

import os

import sqlalchemy as sa
from alembic import op

revision = "0007_import_lignes"
down_revision = "0006_drop_psalaire_derive"
branch_labels = None
depends_on = None

APP_USER = os.environ.get("POSTGRES_APP_USER", "smartkids_app")


def upgrade() -> None:
    op.create_table(
        "import_lignes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("hash", sa.Text, nullable=False, unique=True),
        sa.Column("sheet", sa.Text, nullable=False),
        sa.Column("row_index", sa.Integer, nullable=False),
        sa.Column("entity_type", sa.Text, nullable=True),
        sa.Column("entity_id", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_import_sheet", "import_lignes", ["sheet"])
    op.create_index("ix_import_created", "import_lignes", ["created_at"])
    op.execute(f"GRANT SELECT, INSERT ON import_lignes TO {APP_USER}")


def downgrade() -> None:
    op.drop_index("ix_import_created", table_name="import_lignes")
    op.drop_index("ix_import_sheet", table_name="import_lignes")
    op.drop_table("import_lignes")