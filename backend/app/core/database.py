from collections.abc import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# Todas las tablas de Colmena viven en el esquema `colmena` (ver
# colmena_postgresql_schema.sql). Para engines que no soportan esquemas
# (SQLite en tests), se remapea vía execution_options(schema_translate_map=...).
COLMENA_SCHEMA = "colmena"

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarativa compartida por todos los modelos del esquema `colmena`."""

    metadata = MetaData(schema=COLMENA_SCHEMA)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
