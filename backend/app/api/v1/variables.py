from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import Page, PageParams, page_params
from app.schemas.variables import (
    ExogenousFieldCreate,
    ExogenousFieldRead,
    VariableBatchUpdate,
    VariableCreate,
    VariableRead,
    VariableUpdate,
)
from app.services.variable_service import VariableService

router = APIRouter(tags=["variables"])


@router.get(
    "/projects/{project_id}/exogenous-fields", response_model=list[ExogenousFieldRead]
)
async def list_exogenous_fields(
    project_id: int, session: AsyncSession = Depends(get_db)
):
    service = VariableService(session)
    fields = await service.list_exogenous_fields(project_id)
    return [
        ExogenousFieldRead(
            variable=VariableRead.model_validate(variable),
            question=field,
        )
        for variable, field in fields
    ]


@router.post(
    "/projects/{project_id}/exogenous-fields",
    response_model=ExogenousFieldRead,
    status_code=201,
)
async def create_exogenous_field(
    project_id: int,
    payload: ExogenousFieldCreate,
    session: AsyncSession = Depends(get_db),
):
    service = VariableService(session)
    variable, question = await service.create_exogenous_field(project_id, payload)
    return ExogenousFieldRead(variable=VariableRead.model_validate(variable), question=question)


@router.get("/projects/{project_id}/variables", response_model=Page[VariableRead])
async def list_variables(
    project_id: int,
    params: PageParams = Depends(page_params),
    session: AsyncSession = Depends(get_db),
):
    service = VariableService(session)
    return await service.list_by_project(project_id, params)


@router.post("/projects/{project_id}/variables", response_model=VariableRead, status_code=201)
async def create_variable(
    project_id: int, payload: VariableCreate, session: AsyncSession = Depends(get_db)
):
    service = VariableService(session)
    variable = await service.create(project_id, payload)
    return VariableRead.model_validate(variable)


@router.patch("/projects/{project_id}/variables/batch", response_model=list[VariableRead])
async def batch_update_variables(
    project_id: int, payload: VariableBatchUpdate, session: AsyncSession = Depends(get_db)
):
    service = VariableService(session)
    variables = await service.batch_update(project_id, payload)
    return [VariableRead.model_validate(v) for v in variables]


@router.get("/variables/{variable_id}", response_model=VariableRead)
async def get_variable(variable_id: int, session: AsyncSession = Depends(get_db)):
    service = VariableService(session)
    variable = await service.get(variable_id)
    return VariableRead.model_validate(variable)


@router.patch("/variables/{variable_id}", response_model=VariableRead)
async def update_variable(
    variable_id: int, payload: VariableUpdate, session: AsyncSession = Depends(get_db)
):
    service = VariableService(session)
    variable = await service.update(variable_id, payload)
    return VariableRead.model_validate(variable)


@router.delete("/variables/{variable_id}", status_code=204)
async def delete_variable(variable_id: int, session: AsyncSession = Depends(get_db)):
    service = VariableService(session)
    await service.delete(variable_id)
