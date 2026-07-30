"""add objective and application_mode columns to form_instruments

Campos necesarios para la ficha técnica del instrumento: el objetivo que
mide el instrumento y su modo de aplicación (autoadministrado, individual,
colectivo, etc.).

Revision ID: 20260726_15
Revises: 20260716_14
Create Date: 2026-07-26 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260726_15"
down_revision: Union[str, Sequence[str], None] = "20260716_14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "form_instruments",
        sa.Column("objective", sa.Text(), nullable=True),
    )
    op.add_column(
        "form_instruments",
        sa.Column("application_mode", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("form_instruments", "application_mode")
    op.drop_column("form_instruments", "objective")
