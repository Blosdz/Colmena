from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.studies import ResponseSessionUnitsRead, ResponseSessionUnitsReplace
from app.schemas.responses import (
    ResponseRead,
    ResponseSessionCompleteRequest,
    ResponseSessionRead,
    ResponseUpsert,
)
from app.services.response_service import ResponseService

router = APIRouter(tags=["responses"])


@router.post(
    "/studies/{study_id}/response-sessions", response_model=ResponseSessionRead, status_code=201
)
async def create_response_session(study_id: int, session: AsyncSession = Depends(get_db)):
    service = ResponseService(session)
    response_session = await service.create_session(study_id)
    return ResponseSessionRead.model_validate(response_session)


@router.put(
    "/response-sessions/{session_id}/units", response_model=ResponseSessionUnitsRead
)
async def replace_response_session_units(
    session_id: int,
    payload: ResponseSessionUnitsReplace,
    session: AsyncSession = Depends(get_db),
):
    unit_ids = await ResponseService(session).replace_session_units(session_id, payload)
    return ResponseSessionUnitsRead(response_session_id=session_id, unit_ids=unit_ids)


@router.put(
    "/response-sessions/{session_id}/responses/{question_id}", response_model=ResponseRead
)
async def upsert_response(
    session_id: int,
    question_id: int,
    payload: ResponseUpsert,
    session: AsyncSession = Depends(get_db),
):
    service = ResponseService(session)
    response = await service.upsert_response(session_id, question_id, payload)
    return ResponseRead.model_validate(response)


@router.post(
    "/response-sessions/{session_id}/complete", response_model=ResponseSessionRead
)
async def complete_response_session(
    session_id: int,
    payload: ResponseSessionCompleteRequest = ResponseSessionCompleteRequest(),
    session: AsyncSession = Depends(get_db),
):
    service = ResponseService(session)
    response_session = await service.complete_session(session_id, payload)
    return ResponseSessionRead.model_validate(response_session)
