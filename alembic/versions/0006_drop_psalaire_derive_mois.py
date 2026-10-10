"""drop trigger trg_psalaires_derive_mois

Revision ID: 0006_drop_psalaire_derive
Revises: 0005_stmt_immutability
Create Date: 2026-10-09
"""
from __future__ import annotations

from alembic import op

revision = "0006_drop_psalaire_derive"
down_revision = "0005_stmt_immutability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # paiements_salaires n'a pas de colonne mois_id : le trigger qui tentait
    # de la dériver plantait au runtime. La localisation du mois est portée
    # par salaire_mensuel_id (FK vers salaires_mensuels.mois_id).
    op.execute("DROP TRIGGER IF EXISTS trg_psalaires_derive_mois ON paiements_salaires;")


def downgrade() -> None:
    op.execute(
        "CREATE TRIGGER trg_psalaires_derive_mois "
        "BEFORE INSERT ON paiements_salaires "
        "FOR EACH ROW EXECUTE FUNCTION derive_mois_operation("
        "'date_paiement', 'parent_paiement_salaire_id', 'date_a_completer');"
    )