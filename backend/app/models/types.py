"""Tipos de columna portables entre PostgreSQL (producción) y SQLite (tests)."""

from sqlalchemy import JSON, BigInteger, Integer
from sqlalchemy.dialects.postgresql import JSONB

JSONVariant = JSON().with_variant(JSONB(), "postgresql")

# SQLite sólo autoincrementa una PK declarada exactamente como `INTEGER
# PRIMARY KEY` (afinidad "INTEGER"); BIGINT no activa ese alias de rowid, así
# que en tests (SQLite) los inserts sin id explícito violarían NOT NULL. En
# Postgres se mantiene BIGSERIAL/BIGINT como en colmena_postgresql_schema.sql.
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")
