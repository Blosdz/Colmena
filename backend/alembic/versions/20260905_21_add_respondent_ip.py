"""add respondent_ip to form_responses

Revision ID: 20260905_21
Revises: 20260905_20
Create Date: 2026-09-05 00:30:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260905_21"
down_revision: Union[str, Sequence[str], None] = "20260905_20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("form_responses", sa.Column("respondent_ip", sa.String(45), nullable=True))


def downgrade() -> None:
    op.drop_column("form_responses", "respondent_ip")
