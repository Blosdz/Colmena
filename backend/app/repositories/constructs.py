from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.construct import Construct, ConstructItem


class ConstructRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, construct_id: int) -> Construct | None:
        return await self.session.get(Construct, construct_id)

    def list_by_version_stmt(self, instrument_version_id: int) -> Select:
        return (
            select(Construct)
            .where(Construct.instrument_version_id == instrument_version_id)
            .order_by(Construct.sort_order.asc().nulls_last(), Construct.id.asc())
        )

    async def list_by_version(self, instrument_version_id: int) -> list[Construct]:
        return list(
            (await self.session.execute(self.list_by_version_stmt(instrument_version_id)))
            .scalars()
            .all()
        )

    async def create(self, construct: Construct) -> Construct:
        self.session.add(construct)
        await self.session.flush()
        return construct

    async def delete(self, construct: Construct) -> None:
        await self.session.delete(construct)

    async def get_item(self, construct_id: int, question_id: int) -> ConstructItem | None:
        return await self.session.get(ConstructItem, (construct_id, question_id))

    async def add_item(self, item: ConstructItem) -> ConstructItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def delete_item(self, item: ConstructItem) -> None:
        await self.session.delete(item)
