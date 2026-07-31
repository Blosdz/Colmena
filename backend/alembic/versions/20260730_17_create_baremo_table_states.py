"""create baremo_table_states table

Revision ID: 20260730_17
Revises: 20260727_16
Create Date: 2026-07-30 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260730_17"
down_revision: Union[str, Sequence[str], None] = "20260727_16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "baremo_table_states",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("form_id", sa.String(36), sa.ForeignKey("forms.id"), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("table_key", sa.String(255), nullable=False),
        sa.Column("group_kind", sa.String(20), nullable=False, server_default="custom"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("rows_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("form_id", "table_key", name="uq_baremo_table_form_key"),
    )
    op.create_index("ix_baremo_table_states_form_id", "baremo_table_states", ["form_id"])
    op.create_index("ix_baremo_table_states_project_id", "baremo_table_states", ["project_id"])
    op.create_index("ix_baremo_table_states_user_id", "baremo_table_states", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_baremo_table_states_user_id", "baremo_table_states")
    op.drop_index("ix_baremo_table_states_project_id", "baremo_table_states")
    op.drop_index("ix_baremo_table_states_form_id", "baremo_table_states")
    op.drop_table("baremo_table_states")
