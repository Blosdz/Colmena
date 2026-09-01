"""Permite varios instrumentos vinculados explícitamente a un proyecto.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-13
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

SCHEMA = "colmena"
SQL_FILE = Path(__file__).resolve().parent / "sql" / "0009_project_instruments.sql"


def upgrade() -> None:
    op.get_bind().exec_driver_sql(SQL_FILE.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {SCHEMA}.ix_instruments_project_id")
    op.execute(f"ALTER TABLE {SCHEMA}.instruments DROP COLUMN project_id")
