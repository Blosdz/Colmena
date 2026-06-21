"""create export artifacts

Revision ID: 20260505_04
Revises: 20260505_02
Create Date: 2026-05-05 23:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_04"
down_revision: Union[str, Sequence[str], None] = "20260505_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "export_artifacts",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("form_id", sa.String(length=36), nullable=True),
        sa.Column("artifact_type", sa.String(length=100), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_export_artifacts_form_id_forms")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_export_artifacts_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_export_artifacts")),
    )
    op.create_index(op.f("ix_export_artifacts_artifact_type"), "export_artifacts", ["artifact_type"], unique=False)
    op.create_index(op.f("ix_export_artifacts_form_id"), "export_artifacts", ["form_id"], unique=False)
    op.create_index(op.f("ix_export_artifacts_project_id"), "export_artifacts", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_export_artifacts_project_id"), table_name="export_artifacts")
    op.drop_index(op.f("ix_export_artifacts_form_id"), table_name="export_artifacts")
    op.drop_index(op.f("ix_export_artifacts_artifact_type"), table_name="export_artifacts")
    op.drop_table("export_artifacts")
