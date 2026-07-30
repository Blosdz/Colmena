"""add variable_classification column to project_variables

Los roles de variable se simplifican a dos: "main" (variable principal) e
"intervening" (variable interviniente, antes "demographic"). La clasificación
metodológica (independiente / dependiente / segmento) pasa a una columna
propia opcional, aplicable a cualquier rol.

Revision ID: 20260716_14
Revises: 20260712_13
Create Date: 2026-07-16 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260716_14"
down_revision: Union[str, Sequence[str], None] = "20260712_13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "project_variables",
        sa.Column("variable_classification", sa.String(length=50), nullable=True),
    )
    # Remapeo de roles legacy al nuevo vocabulario.
    op.execute(
        "UPDATE project_variables SET variable_role = 'main', variable_classification = 'independent' "
        "WHERE variable_role = 'independent'"
    )
    op.execute(
        "UPDATE project_variables SET variable_role = 'main', variable_classification = 'dependent' "
        "WHERE variable_role = 'dependent'"
    )
    op.execute(
        "UPDATE project_variables SET variable_role = 'main' "
        "WHERE variable_role IN ('control', 'covariate', 'moderator', 'mediator')"
    )
    op.execute(
        "UPDATE project_variables SET variable_role = 'intervening' "
        "WHERE variable_role = 'demographic'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE project_variables SET variable_role = 'independent' "
        "WHERE variable_role = 'main' AND variable_classification = 'independent'"
    )
    op.execute(
        "UPDATE project_variables SET variable_role = 'dependent' "
        "WHERE variable_role = 'main' AND variable_classification = 'dependent'"
    )
    op.execute(
        "UPDATE project_variables SET variable_role = 'demographic' "
        "WHERE variable_role = 'intervening'"
    )
    op.drop_column("project_variables", "variable_classification")
