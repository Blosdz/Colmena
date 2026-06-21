"""create projects table

Revision ID: 20260505_01
Revises:
Create Date: 2026-05-05 19:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("subtitle", sa.String(length=255), nullable=True),
        sa.Column("research_type", sa.String(length=100), nullable=True),
        sa.Column("design_type", sa.String(length=150), nullable=True),
        sa.Column("approach", sa.String(length=100), nullable=True),
        sa.Column("institution", sa.String(length=255), nullable=True),
        sa.Column("faculty", sa.String(length=255), nullable=True),
        sa.Column("career", sa.String(length=255), nullable=True),
        sa.Column("advisor_name", sa.String(length=255), nullable=True),
        sa.Column("population_description", sa.Text(), nullable=True),
        sa.Column("sample_size_planned", sa.Integer(), nullable=True),
        sa.Column("sample_size_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )
    op.create_index(op.f("ix_projects_deleted_at"), "projects", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_projects_status"), "projects", ["status"], unique=False)
    op.create_index(op.f("ix_projects_title"), "projects", ["title"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_title"), table_name="projects")
    op.drop_index(op.f("ix_projects_status"), table_name="projects")
    op.drop_index(op.f("ix_projects_deleted_at"), table_name="projects")
    op.drop_table("projects")
