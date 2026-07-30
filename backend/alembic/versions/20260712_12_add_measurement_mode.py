"""add measurement_mode column to project_variables

El nivel de medición ya no lo elige el usuario: se deriva de cómo se mide la
variable. Guardamos esa elección ("instrument" | "direct") en measurement_mode.

Revision ID: 20260712_12
Revises: 20260628_11
Create Date: 2026-07-12 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260712_12"
down_revision: Union[str, Sequence[str], None] = "20260628_11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "project_variables",
        sa.Column(
            "measurement_mode",
            sa.String(length=50),
            nullable=False,
            server_default="instrument",
        ),
    )


def downgrade() -> None:
    op.drop_column("project_variables", "measurement_mode")
