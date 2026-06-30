"""add data_base64 column to export_artifacts

Permite persistir el gráfico (data-URL base64) directamente en la BD para que
AppThesis lo consuma vía proxy sin depender del archivo en disco.

Revision ID: 20260628_11
Revises: 20260628_10
Create Date: 2026-06-28 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260628_11"
down_revision: Union[str, Sequence[str], None] = "20260628_10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("export_artifacts", sa.Column("data_base64", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("export_artifacts", "data_base64")
