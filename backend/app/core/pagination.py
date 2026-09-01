from __future__ import annotations

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

T = TypeVar("T")

settings = get_settings()


class PageParams(BaseModel):
    page: int = 1
    page_size: int = settings.default_page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


async def paginate(
    session: AsyncSession,
    stmt: Select,
    params: PageParams,
) -> tuple[list, int]:
    # `with_only_columns(func.count())` pierde el FROM (count() no referencia
    # ninguna columna de tabla), y Postgres evalúa `SELECT count(*)` sin FROM
    # como una sola fila implícita -> total siempre 1 sin importar los datos
    # reales. Envolver el statement original como subquery preserva FROM/JOIN/WHERE.
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    paged_stmt = stmt.offset(params.offset).limit(params.page_size)
    rows = (await session.execute(paged_stmt)).scalars().all()

    return list(rows), total
