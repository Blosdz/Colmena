"""create chart_editor_states table

Revision ID: 20260619_08
Revises: 20260528_07
Create Date: 2026-06-19 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260619_08"
down_revision: Union[str, Sequence[str], None] = "20260528_07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chart_editor_states",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("form_id", sa.String(36), sa.ForeignKey("forms.id"), nullable=False),
        sa.Column("chart_id", sa.String(255), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("graphs_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chart_editor_states_form_id", "chart_editor_states", ["form_id"])
    op.create_index("ix_chart_editor_states_project_id", "chart_editor_states", ["project_id"])
    op.create_index("ix_chart_editor_states_storage_key", "chart_editor_states", ["storage_key"])
    op.create_unique_constraint(
        "uq_chart_editor_form_chart",
        "chart_editor_states",
        ["form_id", "chart_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_chart_editor_form_chart", "chart_editor_states", type_="unique")
    op.drop_index("ix_chart_editor_states_storage_key", "chart_editor_states")
    op.drop_index("ix_chart_editor_states_project_id", "chart_editor_states")
    op.drop_index("ix_chart_editor_states_form_id", "chart_editor_states")
    op.drop_table("chart_editor_states")
