"""Plan Preventivo: trazabilidad al AnalysisRun + hipótesis de origen + enum de estado.

`action_plan_items.finding` (hallazgo) y `action_description` (medida)
existían, pero no había un campo separado para la hipótesis de origen — se
fusionaba con el hallazgo. Tampoco había vínculo con el `AnalysisRun`
canónico que originó la acción (solo `construct_id`, sin saber de qué
corrida de análisis venía). `status` era un `VARCHAR` libre sin restricción;
`OVERDUE` nunca se persiste — es un estado derivado calculado en
`app/core/action_plan_status.py`, por eso el CHECK no lo incluye.

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

SCHEMA = "colmena"


def upgrade() -> None:
    op.add_column(
        "action_plan_items",
        sa.Column("origin_hypothesis", sa.Text(), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "action_plan_items",
        sa.Column("analysis_run_id", sa.BigInteger(), nullable=True),
        schema=SCHEMA,
    )
    op.create_foreign_key(
        "fk_action_plan_items_analysis_run_id",
        "action_plan_items",
        "analysis_runs",
        ["analysis_run_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_action_plan_items_status",
        "action_plan_items",
        "status IN ('PENDING', 'IN_PROGRESS', 'DONE', 'BLOCKED', 'CANCELLED')",
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_action_plan_items_status", "action_plan_items", type_="check", schema=SCHEMA
    )
    op.drop_constraint(
        "fk_action_plan_items_analysis_run_id",
        "action_plan_items",
        type_="foreignkey",
        schema=SCHEMA,
    )
    op.drop_column("action_plan_items", "analysis_run_id", schema=SCHEMA)
    op.drop_column("action_plan_items", "origin_hypothesis", schema=SCHEMA)
