"""add password_hash to users (login standalone de Colmena)

Revision ID: 20260904_19
Revises: 20260807_18
Create Date: 2026-09-04 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260904_19"
down_revision: Union[str, Sequence[str], None] = "20260807_18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
