from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chart import (
    ChartBatchRead,
    ChartBatchRequest,
    ChartExportRead,
    ChartExportRequest,
    ChartGenerateRequest,
    ChartOptionsRead,
    ChartSpecRead,
)
from app.services.chart_service import ChartService


router = APIRouter(tags=["charts"])


def get_chart_service(db: Session = Depends(get_db)) -> ChartService:
    return ChartService(db)


@router.post("/api/v1/forms/{form_id}/charts/generate", response_model=ChartSpecRead)
def generate_chart(
    form_id: str,
    payload: ChartGenerateRequest,
    service: ChartService = Depends(get_chart_service),
) -> ChartSpecRead:
    return service.generate_chart(form_id, payload)


@router.post("/api/v1/forms/{form_id}/charts/batch", response_model=ChartBatchRead)
def generate_chart_batch(
    form_id: str,
    payload: ChartBatchRequest,
    service: ChartService = Depends(get_chart_service),
) -> ChartBatchRead:
    return service.generate_chart_batch(form_id, payload)


@router.post("/api/v1/forms/{form_id}/charts/from-analysis-run/{analysis_run_id}", response_model=ChartBatchRead)
def generate_charts_from_analysis_run(
    form_id: str,
    analysis_run_id: str,
    service: ChartService = Depends(get_chart_service),
) -> ChartBatchRead:
    return service.generate_from_analysis_run(
        form_id,
        analysis_run_id,
        theme="colmena_premium",
        decimals=3,
        include_discarded=False,
        score_aggregation="mean",
    )


@router.post("/api/v1/forms/{form_id}/charts/from-orchestrated-run/{analysis_run_id}", response_model=ChartBatchRead)
def generate_charts_from_orchestrated_run(
    form_id: str,
    analysis_run_id: str,
    service: ChartService = Depends(get_chart_service),
) -> ChartBatchRead:
    return service.generate_from_orchestrated_run(
        form_id,
        analysis_run_id,
        theme="colmena_premium",
        decimals=3,
        include_discarded=False,
        score_aggregation="mean",
    )


@router.get("/api/v1/forms/{form_id}/charts/recommended", response_model=ChartBatchRead)
def get_recommended_charts(
    form_id: str,
    theme: str = Query(default="colmena_premium"),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = False,
    max_charts: int = Query(default=10, ge=1, le=20),
    service: ChartService = Depends(get_chart_service),
) -> ChartBatchRead:
    return service.generate_recommended_charts(
        form_id,
        theme=theme,
        decimals=decimals,
        include_discarded=include_discarded,
        score_aggregation="mean",
        max_charts=max_charts,
    )


@router.get("/api/v1/forms/{form_id}/charts/options", response_model=ChartOptionsRead)
def get_chart_options(
    form_id: str,
    service: ChartService = Depends(get_chart_service),
) -> ChartOptionsRead:
    return service.list_chart_options(form_id)


@router.post("/api/v1/forms/{form_id}/charts/export/json", response_model=ChartExportRead)
def export_chart_json(
    form_id: str,
    payload: ChartExportRequest,
    service: ChartService = Depends(get_chart_service),
) -> ChartExportRead:
    return service.export_chart_specs(form_id, payload)
