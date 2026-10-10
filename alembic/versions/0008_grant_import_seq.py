"""grant usage on import_lignes_id_seq

Revision ID: 0008_grant_import_seq
Revises: 0007_import_lignes
Create Date: 2026-10-10
"""
from __future__ import annotations

import os

from alembic import op

revision = "0008_grant_import_seq"
down_revision = "0007_import_lignes"
branch_labels = None
depends_on = None

APP_USER = os.environ.get("POSTGRES_APP_USER", "smartkids_app")


def upgrade() -> None:
    op.execute(
        f"GRANT USAGE, SELECT ON SEQUENCE import_lignes_id_seq TO {APP_USER}"
    )
    # Sécurité : accorder par défaut USAGE aux futures séquences créées par
    # le rôle owner dans le schéma public. Corrige la cause racine.
    op.execute(
        f"ALTER DEFAULT PRIVILEGES FOR ROLE smartkids_owner IN SCHEMA public "
        f"GRANT USAGE, SELECT ON SEQUENCES TO {APP_USER}"
    )


def downgrade() -> None:
    op.execute(
        f"REVOKE USAGE, SELECT ON SEQUENCE import_lignes_id_seq FROM {APP_USER}"
    )
    op.execute(
        f"ALTER DEFAULT PRIVILEGES FOR ROLE smartkids_owner IN SCHEMA public "
        f"REVOKE USAGE, SELECT ON SEQUENCES FROM {APP_USER}"
    )