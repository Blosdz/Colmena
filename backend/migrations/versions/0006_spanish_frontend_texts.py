"""Normaliza al español los textos persistidos expuestos al frontend.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-13
"""

from __future__ import annotations

from pathlib import Path

from alembic import op


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent / "sql" / "0006_spanish_frontend_texts.sql"


def upgrade() -> None:
    # Alembic usa psycopg síncrono; admite el lote SQL igual que la migración 0001.
    op.get_bind().exec_driver_sql(SQL_FILE.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute(
        "ALTER TABLE colmena.barem_cutoffs "
        "ALTER COLUMN favorable_label SET DEFAULT 'FAVORABLE', "
        "ALTER COLUMN intermediate_label SET DEFAULT 'INTERMEDIATE', "
        "ALTER COLUMN unfavorable_label SET DEFAULT 'UNFAVORABLE'"
    )
    op.execute(
        "UPDATE colmena.barem_cutoffs SET intermediate_label = 'INTERMEDIATE' "
        "WHERE intermediate_label = 'INTERMEDIO'"
    )
    op.execute(
        "UPDATE colmena.barem_cutoffs SET unfavorable_label = 'UNFAVORABLE' "
        "WHERE unfavorable_label = 'DESFAVORABLE'"
    )
    op.execute(
        "UPDATE colmena.barem_bands SET label = CASE label "
        "WHEN 'INTERMEDIO' THEN 'INTERMEDIATE' "
        "WHEN 'DESFAVORABLE' THEN 'UNFAVORABLE' ELSE label END "
        "WHERE label IN ('INTERMEDIO', 'DESFAVORABLE')"
    )
    for table in ("construct_scores", "construct_results"):
        op.execute(
            f"UPDATE colmena.{table} SET classification = CASE classification "
            "WHEN 'INTERMEDIO' THEN 'INTERMEDIATE' "
            "WHEN 'DESFAVORABLE' THEN 'UNFAVORABLE' ELSE classification END "
            "WHERE classification IN ('INTERMEDIO', 'DESFAVORABLE')"
        )
