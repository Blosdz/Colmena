from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chart_palette import (
    ChartPaletteDeleteResponse,
    ChartPaletteRead,
    ChartPaletteSave,
)
from app.services.chart_palette_service import ChartPaletteService


router = APIRouter(tags=["chart-palettes"])


def get_service(db: Session = Depends(get_db)) -> ChartPaletteService:
    return ChartPaletteService(db)


@router.put(
    "/api/v1/forms/{form_id}/chart-palettes/{chart_key}",
    response_model=ChartPaletteRead,
    status_code=200,
)
def upsert_chart_palette(
    form_id: str,
    chart_key: str,
    payload: ChartPaletteSave,
    service: ChartPaletteService = Depends(get_service),
) -> ChartPaletteRead:
    return service.upsert(form_id, chart_key, payload)


@router.get(
    "/api/v1/forms/{form_id}/chart-palettes/{chart_key}",
    response_model=ChartPaletteRead,
)
def get_chart_palette(
    form_id: str,
    chart_key: str,
    service: ChartPaletteService = Depends(get_service),
) -> ChartPaletteRead:
    return service.get(form_id, chart_key)


@router.delete(
    "/api/v1/forms/{form_id}/chart-palettes/{chart_key}",
    response_model=ChartPaletteDeleteResponse,
)
def delete_chart_palette(
    form_id: str,
    chart_key: str,
    service: ChartPaletteService = Depends(get_service),
) -> ChartPaletteDeleteResponse:
    return service.delete(form_id, chart_key)
