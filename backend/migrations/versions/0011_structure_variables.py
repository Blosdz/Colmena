"""Convierte la raíz de proyecto en variables estructurales seleccionables.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-14
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent / "sql" / "0011_structure_variables.sql"


def upgrade() -> None:
    op.get_bind().exec_driver_sql(SQL_FILE.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute("SET search_path TO colmena, public")
    op.execute(
        "DELETE FROM constructs WHERE construct_type = 'VARIABLE' AND parent_id IS NULL "
        "AND id NOT IN (SELECT MIN(id) FROM constructs WHERE construct_type = 'VARIABLE' "
        "AND parent_id IS NULL GROUP BY instrument_version_id)"
    )
    op.execute(
        """UPDATE constructs
        SET construct_type = 'PROJECT',
            metadata = jsonb_set(
                COALESCE(metadata, '{}'::jsonb),
                '{node_kind}',
                '"PROJECT_ROOT"'::jsonb
            )
        WHERE construct_type = 'VARIABLE' AND parent_id IS NULL"""
    )
    op.execute("ALTER TABLE constructs DROP CONSTRAINT ck_constructs_construct_type")
    op.execute(
        "ALTER TABLE constructs ADD CONSTRAINT ck_constructs_construct_type "
        "CHECK (construct_type IN ('PROJECT','DIMENSION','SUBDIMENSION','SCALE','FACTOR','INDEX'))"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_constructs_project_root_per_version "
        "ON constructs(instrument_version_id) "
        "WHERE construct_type = 'PROJECT' AND parent_id IS NULL"
    )
