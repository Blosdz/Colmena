from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.option_set import OptionSet
from app.models.question import Question


class QuestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, question_id: int) -> Question | None:
        return await self.session.get(Question, question_id)

    def list_by_version_stmt(self, instrument_version_id: int) -> Select:
        return (
            select(Question)
            .where(Question.instrument_version_id == instrument_version_id)
            .order_by(Question.sort_order.asc().nulls_last(), Question.id.asc())
        )

    async def list_by_version(self, instrument_version_id: int) -> list[Question]:
        return list(
            (await self.session.execute(self.list_by_version_stmt(instrument_version_id)))
            .scalars()
            .all()
        )

    async def create(self, question: Question) -> Question:
        self.session.add(question)
        await self.session.flush()
        return question

    async def delete(self, question: Question) -> None:
        await self.session.delete(question)

    async def create_option_set(self, option_set: OptionSet) -> OptionSet:
        self.session.add(option_set)
        await self.session.flush()
        return option_set

    async def get_option_set(self, option_set_id: int) -> OptionSet | None:
        stmt = (
            select(OptionSet)
            .where(OptionSet.id == option_set_id)
            .options(selectinload(OptionSet.options))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_option_sets(self, instrument_version_id: int) -> list[OptionSet]:
        stmt = (
            select(OptionSet)
            .where(OptionSet.instrument_version_id == instrument_version_id)
            .options(selectinload(OptionSet.options))
            .order_by(OptionSet.name, OptionSet.id)
        )
        return list((await self.session.execute(stmt)).scalars().all())
