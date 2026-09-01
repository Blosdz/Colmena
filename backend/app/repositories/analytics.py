from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analysis import AnalysisMethod, AnalysisResult, AnalysisRun


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_methods(self) -> list[AnalysisMethod]:
        stmt = select(AnalysisMethod).where(AnalysisMethod.enabled.is_(True)).order_by(
            AnalysisMethod.category, AnalysisMethod.code
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_method_by_code(self, code: str) -> AnalysisMethod | None:
        stmt = select(AnalysisMethod).where(AnalysisMethod.code == code)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_run(self, run: AnalysisRun) -> AnalysisRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_result(self, result: AnalysisResult) -> AnalysisResult:
        self.session.add(result)
        await self.session.flush()
        return result

    async def get_run(self, run_id: int) -> AnalysisRun | None:
        stmt = (
            select(AnalysisRun)
            .where(AnalysisRun.id == run_id)
            .options(selectinload(AnalysisRun.results))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()
