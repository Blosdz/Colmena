from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.constructs import (
    ConstructBatchUpdate,
    ConstructCreate,
    ConstructItemCreate,
    ConstructItemRead,
    ConstructItemUpdate,
    ConstructRead,
    ConstructUpdate,
    StructureVariableCreate,
    StructureVariableRead,
)
from app.services.construct_service import ConstructService

router = APIRouter(tags=["constructs"])


@router.get(
    "/instrument-versions/{version_id}/structure-variables",
    response_model=list[StructureVariableRead],
)
async def list_structure_variables(
    version_id: int, session: AsyncSession = Depends(get_db)
):
    variables = await ConstructService(session).list_structure_variables(version_id)
    return [
        StructureVariableRead(
            id=variable.id,
            code=variable.code,
            name=variable.name,
            role=(variable.metadata_ or {}).get("role", "INDEPENDENT"),
            sort_order=variable.sort_order,
        )
        for variable in variables
    ]


@router.post(
    "/instrument-versions/{version_id}/structure-variables",
    response_model=StructureVariableRead,
    status_code=201,
)
async def create_structure_variable(
    version_id: int,
    payload: StructureVariableCreate,
    session: AsyncSession = Depends(get_db),
):
    variable = await ConstructService(session).create_structure_variable(version_id, payload)
    return StructureVariableRead(
        id=variable.id,
        code=variable.code,
        name=variable.name,
        role=(variable.metadata_ or {}).get("role", "INDEPENDENT"),
        sort_order=variable.sort_order,
    )


@router.get(
    "/instrument-versions/{version_id}/constructs", response_model=list[ConstructRead]
)
async def list_constructs(version_id: int, session: AsyncSession = Depends(get_db)):
    service = ConstructService(session)
    constructs = await service.list_by_version(version_id)
    return [ConstructRead.model_validate(c) for c in constructs]


@router.post(
    "/instrument-versions/{version_id}/constructs",
    response_model=ConstructRead,
    status_code=201,
)
async def create_construct(
    version_id: int, payload: ConstructCreate, session: AsyncSession = Depends(get_db)
):
    service = ConstructService(session)
    construct = await service.create(version_id, payload)
    return ConstructRead.model_validate(construct)


@router.patch(
    "/instrument-versions/{version_id}/constructs/batch", response_model=list[ConstructRead]
)
async def batch_update_constructs(
    version_id: int, payload: ConstructBatchUpdate, session: AsyncSession = Depends(get_db)
):
    service = ConstructService(session)
    constructs = await service.batch_update(version_id, payload)
    return [ConstructRead.model_validate(c) for c in constructs]


@router.get("/constructs/{construct_id}", response_model=ConstructRead)
async def get_construct(construct_id: int, session: AsyncSession = Depends(get_db)):
    service = ConstructService(session)
    construct = await service.get(construct_id)
    return ConstructRead.model_validate(construct)


@router.patch("/constructs/{construct_id}", response_model=ConstructRead)
async def update_construct(
    construct_id: int, payload: ConstructUpdate, session: AsyncSession = Depends(get_db)
):
    service = ConstructService(session)
    construct = await service.update(construct_id, payload)
    return ConstructRead.model_validate(construct)


@router.delete("/constructs/{construct_id}", status_code=204)
async def delete_construct(construct_id: int, session: AsyncSession = Depends(get_db)):
    service = ConstructService(session)
    await service.delete(construct_id)


@router.post(
    "/constructs/{construct_id}/items", response_model=ConstructItemRead, status_code=201
)
async def add_construct_item(
    construct_id: int, payload: ConstructItemCreate, session: AsyncSession = Depends(get_db)
):
    service = ConstructService(session)
    item = await service.add_item(construct_id, payload)
    return ConstructItemRead.model_validate(item)


@router.patch(
    "/constructs/{construct_id}/items/{question_id}", response_model=ConstructItemRead
)
async def update_construct_item(
    construct_id: int,
    question_id: int,
    payload: ConstructItemUpdate,
    session: AsyncSession = Depends(get_db),
):
    service = ConstructService(session)
    item = await service.update_item(construct_id, question_id, payload)
    return ConstructItemRead.model_validate(item)


@router.delete("/constructs/{construct_id}/items/{question_id}", status_code=204)
async def remove_construct_item(
    construct_id: int, question_id: int, session: AsyncSession = Depends(get_db)
):
    service = ConstructService(session)
    await service.remove_item(construct_id, question_id)
