"""Vincula variables derivadas con sus constructos.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

SCHEMA = "colmena"


def upgrade() -> None:
    op.add_column(
        "variables",
        sa.Column("construct_id", sa.BigInteger(), nullable=True),
        schema=SCHEMA,
    )
    op.create_foreign_key(
        "fk_variables_construct_id",
        "variables",
        "constructs",
        ["construct_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="CASCADE",
    )
    op.create_index(
        "idx_variables_construct",
        "variables",
        ["construct_id"],
        schema=SCHEMA,
    )
    op.create_unique_constraint(
        "uq_variables_project_construct",
        "variables",
        ["project_id", "construct_id"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_variables_project_construct", "variables", schema=SCHEMA, type_="unique"
    )
    op.drop_index("idx_variables_construct", table_name="variables", schema=SCHEMA)
    op.drop_constraint(
        "fk_variables_construct_id", "variables", schema=SCHEMA, type_="foreignkey"
    )
    op.drop_column("variables", "construct_id", schema=SCHEMA)
