from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.response_descriptives import ResponseDescriptives
from app.schemas.telemetry import ProjectTelemetry, StudyTelemetry
from app.services.response_descriptive_service import ResponseDescriptiveService
from app.services.telemetry_service import TelemetryService

router = APIRouter(tags=["telemetry"])


@router.get("/studies/{study_id}/response-descriptives", response_model=ResponseDescriptives)
async def get_response_descriptives(
    study_id: int, session: AsyncSession = Depends(get_db)
):
    return await ResponseDescriptiveService(session).get(study_id)


@router.get("/studies/{study_id}/telemetry", response_model=StudyTelemetry)
async def get_study_telemetry(study_id: int, session: AsyncSession = Depends(get_db)):
    service = TelemetryService(session)
    return await service.get_study_telemetry(study_id)


@router.get("/projects/{project_id}/telemetry", response_model=ProjectTelemetry)
async def get_project_telemetry(project_id: int, session: AsyncSession = Depends(get_db)):
    service = TelemetryService(session)
    return await service.get_project_telemetry(project_id)
