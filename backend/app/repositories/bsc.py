from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bsc import ActionPlan, ActionPlanItem, Kpi, KpiMeasurement


class BscRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_action_plan(self, action_plan_id: int) -> ActionPlan | None:
        return await self.session.get(ActionPlan, action_plan_id)

    async def list_action_plans(self, study_id: int) -> list[ActionPlan]:
        stmt = select(ActionPlan).where(ActionPlan.study_id == study_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def add_action_plan(self, plan: ActionPlan) -> ActionPlan:
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def get_item(self, item_id: int) -> ActionPlanItem | None:
        return await self.session.get(ActionPlanItem, item_id)

    async def add_item(self, item: ActionPlanItem) -> ActionPlanItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_items(self, action_plan_id: int) -> list[ActionPlanItem]:
        stmt = select(ActionPlanItem).where(ActionPlanItem.action_plan_id == action_plan_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def add_kpi(self, kpi: Kpi) -> Kpi:
        self.session.add(kpi)
        await self.session.flush()
        return kpi

    async def list_kpis(self, study_id: int) -> list[Kpi]:
        stmt = (
            select(Kpi)
            .where(Kpi.study_id == study_id)
            .options(selectinload(Kpi.measurements))
            .order_by(Kpi.id)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_kpi(self, kpi_id: int) -> Kpi | None:
        stmt = select(Kpi).where(Kpi.id == kpi_id).options(selectinload(Kpi.measurements))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def add_measurement(self, measurement: KpiMeasurement) -> KpiMeasurement:
        self.session.add(measurement)
        await self.session.flush()
        return measurement

    async def list_measurements(self, kpi_id: int) -> list[KpiMeasurement]:
        stmt = (
            select(KpiMeasurement)
            .where(KpiMeasurement.kpi_id == kpi_id)
            .order_by(KpiMeasurement.measured_at.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())
