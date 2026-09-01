"""El valor de tipo "CENSOPAS" pasa a llamarse "CENSO".

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-13

Ver migrations/versions/sql/0008_rename_censopas_to_censo.sql para el
razonamiento: CENSOPAS es el nombre propio de un instituto, no un valor
genérico de project_type/study_type/survey_type.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

SCHEMA = "colmena"
SQL_FILE = Path(__file__).resolve().parent / "sql" / "0008_rename_censopas_to_censo.sql"


def upgrade() -> None:
    op.get_bind().exec_driver_sql(SQL_FILE.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute(f"ALTER TABLE {SCHEMA}.projects DROP CONSTRAINT projects_project_type_check")
    op.execute(f"UPDATE {SCHEMA}.projects SET project_type = 'CENSOPAS' WHERE project_type = 'CENSO'")
    op.execute(
        f"ALTER TABLE {SCHEMA}.projects ADD CONSTRAINT projects_project_type_check "
        "CHECK (project_type IN ('ACADEMIC', 'CENSOPAS', 'CUSTOM', 'RESEARCH'))"
    )

    op.execute(f"ALTER TABLE {SCHEMA}.studies DROP CONSTRAINT studies_study_type_check")
    op.execute(f"UPDATE {SCHEMA}.studies SET study_type = 'CENSOPAS' WHERE study_type = 'CENSO'")
    op.execute(
        f"ALTER TABLE {SCHEMA}.studies ADD CONSTRAINT studies_study_type_check "
        "CHECK (study_type IN ('ACADEMIC', 'CENSOPAS', 'CUSTOM', 'RESEARCH'))"
    )

    op.execute(f"ALTER TABLE {SCHEMA}.surveys DROP CONSTRAINT surveys_survey_type_check")
    op.execute(f"UPDATE {SCHEMA}.surveys SET survey_type = 'CENSOPAS' WHERE survey_type = 'CENSO'")
    op.execute(
        f"ALTER TABLE {SCHEMA}.surveys ADD CONSTRAINT surveys_survey_type_check "
        "CHECK (survey_type IN ('CUSTOM', 'ACADEMIC', 'CENSOPAS', 'INSTRUMENT'))"
    )
