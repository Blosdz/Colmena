"""create users table (cross-login AppThesis)

Revision ID: 20260621_09
Revises: 20260619_08
Create Date: 2026-06-21 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260621_09"
down_revision: Union[str, Sequence[str], None] = "20260619_08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("username", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("appthesis_user_id", sa.String(36), nullable=True),
        sa.Column("thesis_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("appthesis_user_id", name="uq_users_appthesis_user_id"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_appthesis_user_id", "users", ["appthesis_user_id"])
    op.create_index("ix_users_thesis_id", "users", ["thesis_id"])
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_users_deleted_at", "users")
    op.drop_index("ix_users_thesis_id", "users")
    op.drop_index("ix_users_appthesis_user_id", "users")
    op.drop_index("ix_users_email", "users")
    op.drop_index("ix_users_username", "users")
    op.drop_table("users")
