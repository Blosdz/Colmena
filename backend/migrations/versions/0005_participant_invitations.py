"""Token de invitación de un solo uso para encuestas públicas (E-17).

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-13

Las tablas `participants` y `study_invitations` ya existen en Postgres desde
la migración 0001 (creadas por el DDL crudo de
`migrations/versions/sql/0001_colmena_schema.sql`, §12) — nunca tuvieron
modelo SQLAlchemy hasta ahora (`app/models/participant.py`). No se vuelven a
crear aquí (evita chocar con el `IF NOT EXISTS` ya aplicado); esta migración
sólo añade la columna nueva `studies.requires_invitation` (opt-in, harness
§17 de esta corrección) y deja documentado que Participant/StudyInvitation
ya tienen tabla real en Postgres. En SQLite (tests), ambas tablas se crean
por primera vez vía `Base.metadata.create_all()`, ahora que tienen modelo.
"""

from alembic import op
import sqlalchemy as sa


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

SCHEMA = "colmena"


def upgrade() -> None:
    op.add_column(
        "studies",
        sa.Column(
            "requires_invitation",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("studies", "requires_invitation", schema=SCHEMA)
