"""form_theme pasa de surveys.settings a projects.metadata.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-13

Migración de datos, sin cambio de esquema (ambas columnas ya eran JSON/B).
Ver migrations/versions/sql/0007_form_theme_project_scope.sql para el
razonamiento: el estilo del formulario público quedaba guardado en la fila
de Survey equivocada porque un proyecto puede acumular varias, y el Study
abierto al público no necesariamente apunta a la más reciente.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

SCHEMA = "colmena"
SQL_FILE = Path(__file__).resolve().parent / "sql" / "0007_form_theme_project_scope.sql"


def upgrade() -> None:
    op.get_bind().exec_driver_sql(SQL_FILE.read_text(encoding="utf-8"))


def downgrade() -> None:
    # Mejor esfuerzo: la ubicación anterior era por-survey, no por-proyecto,
    # así que se reparte el mismo form_theme a todos los surveys del
    # proyecto (no hay forma de reconstruir cuál survey lo tenía original).
    op.execute(
        f"UPDATE {SCHEMA}.surveys AS s "
        f"SET settings = jsonb_set(s.settings, '{{form_theme}}', p.metadata -> 'form_theme', true) "
        f"FROM {SCHEMA}.projects AS p "
        "WHERE s.project_id = p.id AND p.metadata ? 'form_theme'"
    )
    op.execute(f"UPDATE {SCHEMA}.projects SET metadata = metadata - 'form_theme' WHERE metadata ? 'form_theme'")
