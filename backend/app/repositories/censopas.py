from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.censopas import Barem, BaremBand, BaremCutoff, ConstructResult, ConstructScore, ResponseScore
from app.models.scoring import ScoringRule


class CensopasRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_scoring_rules(self, instrument_version_id: int) -> list[ScoringRule]:
        stmt = select(ScoringRule).where(ScoringRule.instrument_version_id == instrument_version_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_scoring_rule_for_question(self, instrument_version_id: int, question_id: int) -> ScoringRule | None:
        stmt = select(ScoringRule).where(
            ScoringRule.instrument_version_id == instrument_version_id,
            ScoringRule.question_id == question_id,
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def add_scoring_rule(self, rule: ScoringRule) -> ScoringRule:
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def add_barem(self, barem: Barem) -> Barem:
        self.session.add(barem)
        await self.session.flush()
        return barem

    async def get_barem(self, barem_id: int) -> Barem | None:
        stmt = (
            select(Barem)
            .where(Barem.id == barem_id)
            .options(selectinload(Barem.cutoffs), selectinload(Barem.bands))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_barems(self, instrument_version_id: int) -> list[Barem]:
        stmt = (
            select(Barem)
            .where(Barem.instrument_version_id == instrument_version_id)
            .options(selectinload(Barem.bands))
            .order_by(Barem.created_at.desc(), Barem.id.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def add_band(self, band: BaremBand) -> BaremBand:
        self.session.add(band)
        await self.session.flush()
        return band

    async def add_construct_score(self, score: ConstructScore) -> ConstructScore:
        self.session.add(score)
        await self.session.flush()
        return score

    async def add_cutoff(self, cutoff: BaremCutoff) -> BaremCutoff:
        self.session.add(cutoff)
        await self.session.flush()
        return cutoff

    async def add_response_score(self, score: ResponseScore) -> ResponseScore:
        self.session.add(score)
        await self.session.flush()
        return score

    async def add_construct_result(self, result: ConstructResult) -> ConstructResult:
        self.session.add(result)
        await self.session.flush()
        return result

    async def list_construct_results(self, study_id: int) -> list[ConstructResult]:
        stmt = (
            select(ConstructResult)
            .where(ConstructResult.study_id == study_id)
            .options(selectinload(ConstructResult.construct))
            .order_by(ConstructResult.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def delete_existing_results(self, study_id: int) -> None:
        results = await self.list_construct_results(study_id)
        for result in results:
            await self.session.delete(result)
        await self.session.flush()
