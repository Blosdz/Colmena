"""Enlace de usuario con AppThesis (cross-login del monorepo fullProyect).

COLMENA corre dentro del monorepo `fullProyect` junto a AppThesis (thesis-backend
NestJS). El login real lo hace AppThesis; COLMENA valida su JWT contra
`GET {THESIS_API_BASE_URL}/auth/me` y espeja al usuario. `appthesis_user_id`
guarda el UUID de `"AT".usuarios.id`; `thesis_id` la tesis activa del estudiante.
"""

from alembic import op
import sqlalchemy as sa


revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

SCHEMA = "colmena"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("appthesis_user_id", sa.String(64), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "users",
        sa.Column("thesis_id", sa.String(64), nullable=True),
        schema=SCHEMA,
    )
    op.create_unique_constraint(
        "uq_users_appthesis_user_id", "users", ["appthesis_user_id"], schema=SCHEMA
    )
    op.create_index(
        "ix_users_appthesis_user_id", "users", ["appthesis_user_id"], schema=SCHEMA
    )


def downgrade() -> None:
    op.drop_index("ix_users_appthesis_user_id", table_name="users", schema=SCHEMA)
    op.drop_constraint("uq_users_appthesis_user_id", "users", schema=SCHEMA, type_="unique")
    op.drop_column("users", "thesis_id", schema=SCHEMA)
    op.drop_column("users", "appthesis_user_id", schema=SCHEMA)
