"""Reemplaza variables raíz por una única raíz de proyecto.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-14
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

SCHEMA = "colmena"
SQL_FILE = Path(__file__).resolve().parent / "sql" / "0010_project_root.sql"


def upgrade() -> None:
    op.get_bind().exec_driver_sql(SQL_FILE.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute(f"SET search_path TO {SCHEMA}, public")
    op.execute("UPDATE constructs AS child SET parent_id = NULL FROM constructs AS root WHERE child.parent_id = root.id AND root.construct_type = 'PROJECT'")
    op.execute("DELETE FROM constructs WHERE construct_type = 'PROJECT'")
    op.execute("DROP INDEX IF EXISTS uq_constructs_project_root_per_version")
    op.execute("ALTER TABLE constructs DROP CONSTRAINT ck_constructs_construct_type")
    op.execute("ALTER TABLE constructs ADD CONSTRAINT ck_constructs_construct_type CHECK (construct_type IN ('DIMENSION', 'SUBDIMENSION', 'SCALE', 'FACTOR', 'INDEX'))")
