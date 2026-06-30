"""refactor projects: catalogs, demographics 1:1 and owner

Crea los catalogos ``type_research`` / ``design_type`` / ``approach``, la tabla
``project_demographics`` (1:1) y normaliza ``projects``: agrega ``user_id`` (NOT NULL,
FK a users) y los FK de catalogo; mueve la demografia fuera y elimina las columnas
de tipo en texto plano. Incluye seed de catalogos, un usuario por defecto y backfill
de proyectos existentes.

Revision ID: 20260628_10
Revises: 20260621_09
Create Date: 2026-06-28 00:00:00
"""

from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op


revision: str = "20260628_10"
down_revision: Union[str, Sequence[str], None] = "20260621_09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# UUID fijo del usuario por defecto (duenio de proyectos existentes sin owner).
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"

# Valores por defecto sembrados en los catalogos (los que hoy usa el frontend).
RESEARCH_DEFAULTS = ["descriptiva", "correlacional", "comparativa", "explicativa"]
APPROACH_DEFAULTS = ["cuantitativo", "mixto", "cualitativo"]
DESIGN_DEFAULTS = [
    "experimental",
    "cuasi-experimental",
    "no experimental",
    "transversal",
    "longitudinal",
]


def _now_str() -> str:
    # Formato que usa el dialecto SQLite de SQLAlchemy para DateTime.
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")


def _create_catalog_table(name: str) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name", name=f"uq_{name}_name"),
    )
    op.create_index(f"ix_{name}_name", name, ["name"])
    op.create_index(f"ix_{name}_deleted_at", name, ["deleted_at"])


def _seed_catalog(bind, table: str, source_column: str, defaults: list[str]) -> None:
    now = _now_str()
    # Valores distintos ya presentes en projects (texto plano) + los defaults.
    existing = bind.execute(
        sa.text(
            f"SELECT DISTINCT {source_column} FROM projects "
            f"WHERE {source_column} IS NOT NULL AND TRIM({source_column}) <> ''"
        )
    ).scalars().all()

    seen: set[str] = set()
    names: list[str] = []
    for value in [*defaults, *existing]:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        names.append(value.strip())

    for value in names:
        bind.execute(
            sa.text(
                f"INSERT INTO {table} (id, name, is_active, created_at, updated_at) "
                "VALUES (:id, :name, 1, :now, :now)"
            ),
            {"id": str(uuid4()), "name": value, "now": now},
        )


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Catalogos + tabla de demografia.
    _create_catalog_table("type_research")
    _create_catalog_table("design_type")
    _create_catalog_table("approach")

    op.create_table(
        "project_demographics",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", name="fk_project_demographics_project_id_projects"),
            nullable=False,
        ),
        sa.Column("population_description", sa.Text(), nullable=True),
        sa.Column("sample_size_planned", sa.Integer(), nullable=True),
        sa.Column("sample_size_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sampling_method", sa.String(100), nullable=True),
        sa.Column("inclusion_criteria", sa.Text(), nullable=True),
        sa.Column("exclusion_criteria", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("project_id", name="uq_project_demographics_project_id"),
    )
    op.create_index(
        "ix_project_demographics_project_id", "project_demographics", ["project_id"]
    )
    op.create_index(
        "ix_project_demographics_deleted_at", "project_demographics", ["deleted_at"]
    )

    # 2. Seed de catalogos (defaults + valores existentes en projects).
    _seed_catalog(bind, "type_research", "research_type", RESEARCH_DEFAULTS)
    _seed_catalog(bind, "design_type", "design_type", DESIGN_DEFAULTS)
    _seed_catalog(bind, "approach", "approach", APPROACH_DEFAULTS)

    # 3. Usuario por defecto para backfillear proyectos existentes sin owner.
    now = _now_str()
    bind.execute(
        sa.text(
            "INSERT INTO users (id, name, username, email, status, created_at, updated_at) "
            "VALUES (:id, :name, :username, :email, 'active', :now, :now)"
        ),
        {
            "id": DEFAULT_USER_ID,
            "name": "Sistema Colmena",
            "username": "system",
            "email": "system@colmena.local",
            "now": now,
        },
    )

    # 4. Nuevas columnas en projects (nullable temporalmente) + FKs + indices.
    with op.batch_alter_table("projects", schema=None) as batch:
        batch.add_column(sa.Column("user_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("type_research_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("design_type_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("approach_id", sa.String(36), nullable=True))
        batch.create_foreign_key(
            "fk_projects_user_id_users", "users", ["user_id"], ["id"]
        )
        batch.create_foreign_key(
            "fk_projects_type_research_id_type_research",
            "type_research",
            ["type_research_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_projects_design_type_id_design_type",
            "design_type",
            ["design_type_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_projects_approach_id_approach", "approach", ["approach_id"], ["id"]
        )
        batch.create_index("ix_projects_user_id", ["user_id"])
        batch.create_index("ix_projects_type_research_id", ["type_research_id"])
        batch.create_index("ix_projects_design_type_id", ["design_type_id"])
        batch.create_index("ix_projects_approach_id", ["approach_id"])

    # 5. Backfill de proyectos existentes.
    bind.execute(
        sa.text("UPDATE projects SET user_id = :uid WHERE user_id IS NULL"),
        {"uid": DEFAULT_USER_ID},
    )
    for column, table in (
        ("research_type", "type_research"),
        ("design_type", "design_type"),
        ("approach", "approach"),
    ):
        target = "type_research_id" if table == "type_research" else f"{table}_id"
        bind.execute(
            sa.text(
                f"UPDATE projects SET {target} = ("
                f"  SELECT c.id FROM {table} c WHERE c.name = projects.{column}"
                f") WHERE {column} IS NOT NULL AND TRIM({column}) <> ''"
            )
        )

    # project_demographics: una fila por proyecto con la demografia movida.
    projects = bind.execute(
        sa.text(
            "SELECT id, population_description, sample_size_planned, sample_size_current "
            "FROM projects"
        )
    ).all()
    for proj in projects:
        bind.execute(
            sa.text(
                "INSERT INTO project_demographics "
                "(id, project_id, population_description, sample_size_planned, "
                " sample_size_current, created_at, updated_at) "
                "VALUES (:id, :pid, :pop, :planned, :current, :now, :now)"
            ),
            {
                "id": str(uuid4()),
                "pid": proj.id,
                "pop": proj.population_description,
                "planned": proj.sample_size_planned,
                "current": proj.sample_size_current if proj.sample_size_current is not None else 0,
                "now": now,
            },
        )

    # 6. user_id -> NOT NULL y eliminar columnas viejas.
    with op.batch_alter_table("projects", schema=None) as batch:
        batch.alter_column("user_id", existing_type=sa.String(36), nullable=False)
        batch.drop_column("research_type")
        batch.drop_column("design_type")
        batch.drop_column("approach")
        batch.drop_column("population_description")
        batch.drop_column("sample_size_planned")
        batch.drop_column("sample_size_current")


def downgrade() -> None:
    bind = op.get_bind()

    # 1. Recrear columnas viejas en projects.
    with op.batch_alter_table("projects", schema=None) as batch:
        batch.add_column(sa.Column("research_type", sa.String(100), nullable=True))
        batch.add_column(sa.Column("design_type", sa.String(150), nullable=True))
        batch.add_column(sa.Column("approach", sa.String(100), nullable=True))
        batch.add_column(sa.Column("population_description", sa.Text(), nullable=True))
        batch.add_column(sa.Column("sample_size_planned", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column("sample_size_current", sa.Integer(), nullable=False, server_default="0")
        )

    # 2. Recopiar tipos (id->name) y demografia de vuelta a projects.
    for column, table in (
        ("research_type", "type_research"),
        ("design_type", "design_type"),
        ("approach", "approach"),
    ):
        target = "type_research_id" if table == "type_research" else f"{table}_id"
        bind.execute(
            sa.text(
                f"UPDATE projects SET {column} = ("
                f"  SELECT c.name FROM {table} c WHERE c.id = projects.{target}"
                f") WHERE {target} IS NOT NULL"
            )
        )
    bind.execute(
        sa.text(
            "UPDATE projects SET "
            "population_description = ("
            "  SELECT d.population_description FROM project_demographics d "
            "  WHERE d.project_id = projects.id), "
            "sample_size_planned = ("
            "  SELECT d.sample_size_planned FROM project_demographics d "
            "  WHERE d.project_id = projects.id), "
            "sample_size_current = COALESCE(("
            "  SELECT d.sample_size_current FROM project_demographics d "
            "  WHERE d.project_id = projects.id), 0)"
        )
    )

    # 3. Quitar columnas/FKs/indices nuevos de projects.
    with op.batch_alter_table("projects", schema=None) as batch:
        batch.drop_index("ix_projects_approach_id")
        batch.drop_index("ix_projects_design_type_id")
        batch.drop_index("ix_projects_type_research_id")
        batch.drop_index("ix_projects_user_id")
        batch.drop_column("approach_id")
        batch.drop_column("design_type_id")
        batch.drop_column("type_research_id")
        batch.drop_column("user_id")

    # 4. Borrar usuario por defecto y tablas nuevas.
    bind.execute(sa.text("DELETE FROM users WHERE id = :uid"), {"uid": DEFAULT_USER_ID})

    op.drop_index("ix_project_demographics_deleted_at", "project_demographics")
    op.drop_index("ix_project_demographics_project_id", "project_demographics")
    op.drop_table("project_demographics")
    for name in ("approach", "design_type", "type_research"):
        op.drop_index(f"ix_{name}_deleted_at", name)
        op.drop_index(f"ix_{name}_name", name)
        op.drop_table(name)
