"""add metadata_json to forms

Revision ID: 20260528_07
Revises: 20260509_06
Create Date: 2026-05-28 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260528_07"
down_revision: Union[str, Sequence[str], None] = "20260509_06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("forms", sa.Column("metadata_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("forms", "metadata_json")
