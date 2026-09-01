"""Separa el rol de investigación (research_role) del scoring (is_scored) en questions.

`question_role` conflaba tres cosas distintas: si el ítem participa en un
scoring (ya cubierto por `is_scored`), si es un dato de perfil exógeno, y un
catch-all "DESCRIPTIVE" para todo lo demás. Un survey tipo CENSOPAS tiene
muchas preguntas (edad, sexo, remuneración) que no pertenecen a ninguna
variable de investigación, así que el rol debe ser opcional e independiente
de si el ítem se puntúa.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

SCHEMA = "colmena"


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("research_role", sa.String(length=30), nullable=True),
        schema=SCHEMA,
    )
    op.execute(
        "UPDATE colmena.questions SET research_role = 'EXOGENOUS' "
        "WHERE question_role = 'EXOGENOUS'"
    )
    op.create_check_constraint(
        "ck_questions_research_role",
        "questions",
        "research_role IS NULL OR research_role IN "
        "('EXOGENOUS', 'ENDOGENOUS', 'MEDIATOR', 'MODERATOR', 'CONTROL')",
        schema=SCHEMA,
    )
    op.drop_constraint("ck_questions_question_role", "questions", type_="check", schema=SCHEMA)
    op.drop_column("questions", "question_role", schema=SCHEMA)


def downgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("question_role", sa.String(length=30), nullable=False, server_default="DESCRIPTIVE"),
        schema=SCHEMA,
    )
    op.execute(
        "UPDATE colmena.questions SET question_role = 'SCORED' WHERE is_scored IS TRUE"
    )
    op.execute(
        "UPDATE colmena.questions SET question_role = 'EXOGENOUS' "
        "WHERE research_role = 'EXOGENOUS' AND is_scored IS NOT TRUE"
    )
    op.create_check_constraint(
        "ck_questions_question_role",
        "questions",
        "question_role IN ('SCORED', 'EXOGENOUS', 'DESCRIPTIVE')",
        schema=SCHEMA,
    )
    op.drop_constraint("ck_questions_research_role", "questions", type_="check", schema=SCHEMA)
    op.drop_column("questions", "research_role", schema=SCHEMA)
