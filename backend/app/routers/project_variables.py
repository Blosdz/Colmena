from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.project_variable import (
    ProjectVariableCreate,
    ProjectVariableListResponse,
    ProjectVariableRead,
    ProjectVariableUpdate,
)
from app.services.project_variable_service import ProjectVariableService

router = APIRouter(tags=["project-variables"])


def get_project_variable_service(db: Session = Depends(get_db)) -> ProjectVariableService:
    return ProjectVariableService(db)


@router.post("/api/v1/projects/{project_id}/variables", response_model=ProjectVariableRead, status_code=201)
def create_project_variable(
    project_id: str,
    payload: ProjectVariableCreate,
    service: ProjectVariableService = Depends(get_project_variable_service),
) -> ProjectVariableRead:
    return service.create_variable(project_id, payload)


@router.get("/api/v1/projects/{project_id}/variables", response_model=ProjectVariableListResponse)
def list_project_variables(
    project_id: str,
    service: ProjectVariableService = Depends(get_project_variable_service),
) -> ProjectVariableListResponse:
    items, total = service.list_variables(project_id)
    return ProjectVariableListResponse(items=items, total=total)


@router.get("/api/v1/project-variables/{variable_id}", response_model=ProjectVariableRead)
def get_project_variable(
    variable_id: str,
    service: ProjectVariableService = Depends(get_project_variable_service),
) -> ProjectVariableRead:
    return service.get_variable(variable_id)


@router.patch("/api/v1/project-variables/{variable_id}", response_model=ProjectVariableRead)
def update_project_variable(
    variable_id: str,
    payload: ProjectVariableUpdate,
    service: ProjectVariableService = Depends(get_project_variable_service),
) -> ProjectVariableRead:
    return service.update_variable(variable_id, payload)


@router.delete("/api/v1/project-variables/{variable_id}")
def delete_project_variable(
    variable_id: str,
    service: ProjectVariableService = Depends(get_project_variable_service),
) -> dict[str, str]:
    return service.soft_delete_variable(variable_id)
