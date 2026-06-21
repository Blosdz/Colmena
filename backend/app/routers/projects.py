from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.project import ProjectCreate, ProjectListResponse, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    return service.create_project(payload)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
    service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    items, total = service.list_projects(limit=limit, offset=offset, q=q)
    return ProjectListResponse(items=items, total=total)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    return service.get_project(project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    return service.update_project(project_id, payload)


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> dict[str, str]:
    return service.soft_delete_project(project_id)
