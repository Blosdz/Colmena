from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.scale import ScaleCreate, ScaleListResponse, ScaleRead
from app.services.scale_service import ScaleService

router = APIRouter(tags=["scales"])


def get_scale_service(db: Session = Depends(get_db)) -> ScaleService:
    return ScaleService(db)


@router.get("/api/v1/scales", response_model=ScaleListResponse)
def list_scales(
    project_id: str | None = Query(default=None),
    service: ScaleService = Depends(get_scale_service),
) -> ScaleListResponse:
    items, total = service.list_scales(project_id)
    return ScaleListResponse(items=items, total=total)


@router.post("/api/v1/projects/{project_id}/scales", response_model=ScaleRead, status_code=201)
def create_scale(
    project_id: str,
    payload: ScaleCreate,
    service: ScaleService = Depends(get_scale_service),
) -> ScaleRead:
    return service.create_scale(project_id, payload)


@router.get("/api/v1/scales/{scale_id}", response_model=ScaleRead)
def get_scale(
    scale_id: str,
    service: ScaleService = Depends(get_scale_service),
) -> ScaleRead:
    return service.get_scale(scale_id)


@router.delete("/api/v1/scales/{scale_id}")
def delete_scale(
    scale_id: str,
    service: ScaleService = Depends(get_scale_service),
) -> dict[str, str]:
    return service.soft_delete_scale(scale_id)
