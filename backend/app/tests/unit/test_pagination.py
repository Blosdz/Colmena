"""Regresión: `paginate()` debía preservar el FROM de la subquery de conteo.

Bug real encontrado en verificación manual: `stmt.with_only_columns(func.count())`
pierde el FROM (count() no referencia columnas de tabla), y Postgres evalúa
`SELECT count(*)` sin FROM como una fila implícita -> total siempre 1,
sin importar cuántas filas hubiera realmente (o incluso con 0 filas).
"""

from sqlalchemy import select

from app.core.pagination import PageParams, paginate
from app.models.project import Project
from app.models.user import User


async def test_paginate_total_is_zero_with_no_rows(session) -> None:
    stmt = select(Project).order_by(Project.created_at.desc())
    items, total = await paginate(session, stmt, PageParams(page=1, page_size=10))
    assert total == 0
    assert items == []


async def test_paginate_total_matches_actual_row_count(session, seed_user: User) -> None:
    for i in range(3):
        session.add(Project(owner_user_id=seed_user.id, name=f"P{i}", project_type="ACADEMIC"))
    await session.commit()

    stmt = select(Project).order_by(Project.created_at.desc())
    items, total = await paginate(session, stmt, PageParams(page=1, page_size=2))
    assert total == 3
    assert len(items) == 2
