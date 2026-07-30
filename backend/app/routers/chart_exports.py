from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.chart_export_service import ChartExportService

router = APIRouter(tags=["chart-exports"])


def get_chart_export_service(db: Session = Depends(get_db)) -> ChartExportService:
    return ChartExportService(db)


@router.get("/api/v1/forms/{form_id}/chart-exports/baremo-levels/{scoring_config_id}.png")
def render_baremo_levels_export(
    form_id: str,
    scoring_config_id: str,
    service: ChartExportService = Depends(get_chart_export_service),
) -> FileResponse:
    png_path = service.render_baremo_levels_png(form_id, scoring_config_id)
    return FileResponse(png_path, media_type="image/png")


@router.get("/api/v1/forms/{form_id}/chart-exports/normality-histogram/{target_id}.png")
def render_normality_histogram_export(
    form_id: str,
    target_id: str,
    target_type: str = Query(pattern="^(dimension|instrument|project_variable)$"),
    bins: int = Query(default=10, ge=3, le=30),
    service: ChartExportService = Depends(get_chart_export_service),
) -> FileResponse:
    png_path = service.render_normality_histogram_png(form_id, target_type=target_type, target_id=target_id, bins=bins)
    return FileResponse(png_path, media_type="image/png")


@router.get("/api/v1/forms/{form_id}/chart-exports/correlation-scatter.png")
def render_correlation_scatter_export(
    form_id: str,
    x_type: str = Query(pattern="^(question|dimension|instrument|project_variable)$"),
    x_id: str = Query(),
    y_type: str = Query(pattern="^(question|dimension|instrument|project_variable)$"),
    y_id: str = Query(),
    service: ChartExportService = Depends(get_chart_export_service),
) -> FileResponse:
    png_path = service.render_correlation_scatter_png(form_id, x_type=x_type, x_id=x_id, y_type=y_type, y_id=y_id)
    return FileResponse(png_path, media_type="image/png")


@router.get("/api/v1/forms/{form_id}/chart-exports/dimension-bars/{instrument_id}.png")
def render_dimension_coefficient_bars_export(
    form_id: str,
    instrument_id: str,
    y_type: str = Query(pattern="^(question|dimension|instrument|project_variable)$"),
    y_id: str = Query(),
    service: ChartExportService = Depends(get_chart_export_service),
) -> FileResponse:
    png_path = service.render_dimension_coefficient_bars_png(form_id, instrument_id=instrument_id, y_type=y_type, y_id=y_id)
    return FileResponse(png_path, media_type="image/png")
