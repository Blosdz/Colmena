"""create chart_palettes table

Revision ID: 20260807_18
Revises: 20260730_17
Create Date: 2026-08-07 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260807_18"
down_revision: Union[str, Sequence[str], None] = "20260730_17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chart_palettes",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("form_id", sa.String(36), sa.ForeignKey("forms.id"), nullable=False),
        sa.Column("chart_key", sa.String(255), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("colors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("form_id", "chart_key", name="uq_chart_palette_form_chart"),
    )
    op.create_index("ix_chart_palettes_form_id", "chart_palettes", ["form_id"])
    op.create_index("ix_chart_palettes_project_id", "chart_palettes", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_chart_palettes_project_id", "chart_palettes")
    op.drop_index("ix_chart_palettes_form_id", "chart_palettes")
    op.drop_table("chart_palettes")
