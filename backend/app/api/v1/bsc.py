from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.bsc import (
    ActionPlanCreate,
    ActionPlanItemCreate,
    ActionPlanItemRead,
    ActionPlanItemUpdate,
    ActionPlanRead,
    KpiCreate,
    KpiMeasurementCreate,
    KpiMeasurementRead,
    KpiRead,
)
from app.services.bsc_service import BscService

router = APIRouter(tags=["bsc"])


@router.post("/studies/{study_id}/action-plans", response_model=ActionPlanRead, status_code=201)
async def create_action_plan(
    study_id: int, payload: ActionPlanCreate, session: AsyncSession = Depends(get_db)
):
    service = BscService(session)
    plan = await service.create_action_plan(study_id, payload)
    return ActionPlanRead.model_validate(plan)


@router.get("/studies/{study_id}/action-plans", response_model=list[ActionPlanRead])
async def list_action_plans(study_id: int, session: AsyncSession = Depends(get_db)):
    service = BscService(session)
    plans = await service.list_action_plans(study_id)
    return [ActionPlanRead.model_validate(p) for p in plans]


@router.post(
    "/action-plans/{action_plan_id}/items", response_model=ActionPlanItemRead, status_code=201
)
async def add_action_plan_item(
    action_plan_id: int, payload: ActionPlanItemCreate, session: AsyncSession = Depends(get_db)
):
    service = BscService(session)
    item = await service.add_item(action_plan_id, payload)
    return ActionPlanItemRead.model_validate(item)


@router.get("/action-plans/{action_plan_id}/items", response_model=list[ActionPlanItemRead])
async def list_action_plan_items(action_plan_id: int, session: AsyncSession = Depends(get_db)):
    service = BscService(session)
    items = await service.list_items(action_plan_id)
    return [ActionPlanItemRead.model_validate(i) for i in items]


@router.patch("/action-plan-items/{item_id}", response_model=ActionPlanItemRead)
async def update_action_plan_item(
    item_id: int, payload: ActionPlanItemUpdate, session: AsyncSession = Depends(get_db)
):
    service = BscService(session)
    item = await service.update_item(item_id, payload)
    return ActionPlanItemRead.model_validate(item)


@router.post("/studies/{study_id}/kpis", response_model=KpiRead, status_code=201)
async def create_kpi(study_id: int, payload: KpiCreate, session: AsyncSession = Depends(get_db)):
    service = BscService(session)
    kpi = await service.create_kpi(study_id, payload)
    return KpiRead.model_validate(kpi)


@router.get("/studies/{study_id}/kpis", response_model=list[KpiRead])
async def list_kpis(study_id: int, session: AsyncSession = Depends(get_db)):
    service = BscService(session)
    kpis = await service.list_kpis(study_id)
    return [KpiRead.model_validate(k) for k in kpis]


@router.post(
    "/kpis/{kpi_id}/measurements", response_model=KpiMeasurementRead, status_code=201
)
async def add_kpi_measurement(
    kpi_id: int, payload: KpiMeasurementCreate, session: AsyncSession = Depends(get_db)
):
    service = BscService(session)
    measurement = await service.add_measurement(kpi_id, payload)
    return KpiMeasurementRead.model_validate(measurement)


@router.get("/kpis/{kpi_id}/measurements", response_model=list[KpiMeasurementRead])
async def list_kpi_measurements(kpi_id: int, session: AsyncSession = Depends(get_db)):
    service = BscService(session)
    measurements = await service.list_measurements(kpi_id)
    return [KpiMeasurementRead.model_validate(m) for m in measurements]
