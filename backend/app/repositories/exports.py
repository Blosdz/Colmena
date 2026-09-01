from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export import Export


class ExportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, export_id: int) -> Export | None:
        return await self.session.get(Export, export_id)

    async def create(self, export: Export) -> Export:
        self.session.add(export)
        await self.session.flush()
        return export

    async def list_by_study(self, study_id: int) -> list[Export]:
        stmt = (
            select(Export)
            .where(Export.study_id == study_id)
            .order_by(Export.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())
