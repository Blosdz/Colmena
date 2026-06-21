"""create analysis runs

Revision ID: 20260506_05
Revises: 20260505_04
Create Date: 2026-05-06 01:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260506_05"
down_revision: Union[str, Sequence[str], None] = "20260505_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analysis_runs",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("params_json", sa.JSON(), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_analysis_runs_form_id_forms")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_analysis_runs_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analysis_runs")),
    )
    op.create_index(op.f("ix_analysis_runs_form_id"), "analysis_runs", ["form_id"], unique=False)
    op.create_index(op.f("ix_analysis_runs_project_id"), "analysis_runs", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_runs_project_id"), table_name="analysis_runs")
    op.drop_index(op.f("ix_analysis_runs_form_id"), table_name="analysis_runs")
    op.drop_table("analysis_runs")
