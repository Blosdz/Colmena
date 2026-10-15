"""create immutable public form snapshots

Revision ID: 20261002_22
Revises: 20260905_21
Create Date: 2026-10-02 12:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20261002_22"
down_revision: Union[str, Sequence[str], None] = "20260905_21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "form_public_snapshots",
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("form_id", "version", name="uq_form_public_snapshots_version"),
    )
    op.create_index(
        op.f("ix_form_public_snapshots_form_id"),
        "form_public_snapshots",
        ["form_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_form_public_snapshots_is_active"),
        "form_public_snapshots",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_form_public_snapshots_is_active"), table_name="form_public_snapshots")
    op.drop_index(op.f("ix_form_public_snapshots_form_id"), table_name="form_public_snapshots")
    op.drop_table("form_public_snapshots")
