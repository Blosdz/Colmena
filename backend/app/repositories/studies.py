from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.instrument import InstrumentVersion
from app.models.study import Study, StudySnapshot


class StudyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, study_id: int) -> Study | None:
        stmt = (
            select(Study)
            .where(Study.id == study_id)
            .options(
                selectinload(Study.instrument_version).selectinload(
                    InstrumentVersion.instrument
                ),
                selectinload(Study.analytics_plan),
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_with_instrument_version(self, study_id: int) -> Study | None:
        stmt = (
            select(Study)
            .where(Study.id == study_id)
            .options(
                selectinload(Study.instrument_version).selectinload(
                    InstrumentVersion.instrument
                ),
                selectinload(Study.analytics_plan),
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_public_id(self, public_id: uuid.UUID) -> Study | None:
        stmt = select(Study).where(Study.public_id == public_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    def list_by_project_stmt(self, project_id: int) -> Select:
        return (
            select(Study)
            .where(Study.project_id == project_id)
            .options(
                selectinload(Study.instrument_version).selectinload(
                    InstrumentVersion.instrument
                ),
                selectinload(Study.analytics_plan),
            )
            .order_by(Study.created_at.desc())
        )

    async def create(self, study: Study) -> Study:
        self.session.add(study)
        await self.session.flush()
        return study

    async def add_snapshot(self, snapshot: StudySnapshot) -> StudySnapshot:
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot
