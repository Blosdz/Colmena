from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chart_image import (
    ChartImageBase64Read,
    ChartImageDeleteResponse,
    ChartImageListRead,
    ChartImageRead,
    ChartImageUploadRequest,
    ChartImageUploadResponse,
)
from app.services.chart_image_service import ChartImageService


router = APIRouter(tags=["chart-images"])


def get_chart_image_service(db: Session = Depends(get_db)) -> ChartImageService:
    return ChartImageService(db)


@router.post("/api/v1/forms/{form_id}/chart-images", response_model=ChartImageUploadResponse, status_code=201)
def upload_chart_image(
    form_id: str,
    payload: ChartImageUploadRequest,
    service: ChartImageService = Depends(get_chart_image_service),
) -> ChartImageUploadResponse:
    return service.upload_chart_image(form_id, payload)


@router.get("/api/v1/forms/{form_id}/chart-images", response_model=ChartImageListRead)
def list_chart_images(
    form_id: str,
    service: ChartImageService = Depends(get_chart_image_service),
) -> ChartImageListRead:
    return service.list_chart_images(form_id)


@router.get("/api/v1/forms/{form_id}/chart-images/word-ready", response_model=ChartImageListRead)
def list_word_ready_chart_images(
    form_id: str,
    service: ChartImageService = Depends(get_chart_image_service),
) -> ChartImageListRead:
    return service.list_chart_images(form_id, png_only=True)


@router.get(
    "/api/v1/forms/{form_id}/chart-images/{artifact_id}/base64",
    response_model=ChartImageBase64Read,
)
def get_chart_image_base64(
    form_id: str,
    artifact_id: str,
    service: ChartImageService = Depends(get_chart_image_service),
) -> ChartImageBase64Read:
    return service.get_chart_image_base64(form_id, artifact_id)


@router.get("/api/v1/forms/{form_id}/chart-images/{artifact_id}", response_model=ChartImageRead)
def get_chart_image(
    form_id: str,
    artifact_id: str,
    service: ChartImageService = Depends(get_chart_image_service),
) -> ChartImageRead:
    return service.get_chart_image(form_id, artifact_id)


@router.delete("/api/v1/forms/{form_id}/chart-images/{artifact_id}", response_model=ChartImageDeleteResponse)
def delete_chart_image(
    form_id: str,
    artifact_id: str,
    service: ChartImageService = Depends(get_chart_image_service),
) -> ChartImageDeleteResponse:
    return service.delete_chart_image(form_id, artifact_id)
