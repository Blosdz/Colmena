from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey import Survey, SurveyQuestion


class SurveyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, survey_id: int) -> Survey | None:
        return await self.session.get(Survey, survey_id)

    def list_by_project_stmt(self, project_id: int) -> Select:
        return (
            select(Survey)
            .where(Survey.project_id == project_id)
            .order_by(Survey.created_at.desc())
        )

    async def create(self, survey: Survey) -> Survey:
        self.session.add(survey)
        await self.session.flush()
        return survey

    async def delete(self, survey: Survey) -> None:
        await self.session.delete(survey)

    async def add_question(self, link: SurveyQuestion) -> SurveyQuestion:
        self.session.add(link)
        await self.session.flush()
        return link

    async def list_questions(self, survey_id: int) -> list[SurveyQuestion]:
        stmt = (
            select(SurveyQuestion)
            .where(SurveyQuestion.survey_id == survey_id)
            .order_by(SurveyQuestion.sort_order.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())
