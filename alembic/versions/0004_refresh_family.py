"""add refresh_tokens.family_id

Revision ID: 0004_refresh_family
Revises: 0003_views
Create Date: 2026-10-09
"""
from __future__ import annotations

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_refresh_family"
down_revision = "0003_views"
branch_labels = None
depends_on = None

APP_USER = os.environ.get("POSTGRES_APP_USER", "smartkids_app")


def upgrade() -> None:
    op.add_column(
        "refresh_tokens",
        sa.Column("family_id", postgresql.UUID(as_uuid=False), nullable=True),
    )
    op.execute("UPDATE refresh_tokens SET family_id = gen_random_uuid() WHERE family_id IS NULL")
    op.alter_column("refresh_tokens", "family_id", nullable=False)
    op.create_index("ix_refresh_family", "refresh_tokens", ["family_id"])
    op.execute(f"GRANT UPDATE ON refresh_tokens TO {APP_USER}")


def downgrade() -> None:
    op.drop_index("ix_refresh_family", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "family_id")