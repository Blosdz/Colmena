"""Esquema inicial de Colmena: portado de colmena_postgresql_schema.sql + tabla variables.

Revision ID: 0001
Revises:
Create Date: 2026-08-11

Esta migración ejecuta el SQL ya acordado con el usuario
(`colmena_postgresql_schema.sql`, raíz del repo) tal cual, más la tabla
`variables` (harness backend §7), ausente en ese SQL. Se usa `op.execute` en
lugar de operaciones declarativas de Alembic porque el DDL incluye
extensiones, funciones plpgsql, triggers, vistas y datos semilla (catálogo de
métodos + CENSOPAS-COPSOQ) que no tienen representación 1:1 en la API de
Alembic — ver harness §53 ("la primera migración debe reflejar el SQL de
Colmena acordado").
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SQL_DIR = Path(__file__).resolve().parent / "sql"


def _read(filename: str) -> str:
    return (SQL_DIR / filename).read_text(encoding="utf-8")


def upgrade() -> None:
    # `op.execute` envuelve el string en `sqlalchemy.text()`, que interpreta
    # `:identifier` como bind parameter — y el SQL de Colmena contiene
    # literales JSON con colones (`{"key":value}`), que `text()` rompe. Se usa
    # `exec_driver_sql` para enviar el DDL/DML tal cual al driver, sin parseo.
    bind = op.get_bind()
    bind.exec_driver_sql(_read("0001_colmena_schema.sql"))
    bind.exec_driver_sql(_read("0001_variables_table.sql"))


def downgrade() -> None:
    op.get_bind().exec_driver_sql("DROP SCHEMA IF EXISTS colmena CASCADE;")
