from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.apa_table import (
    ApaTableBatchRead,
    ApaTableBatchRequest,
    ApaTableExportRead,
    ApaTableOptionsRead,
    ApaTableRead,
    ApaTableRequest,
)
from app.services.apa_table_service import ApaTableService


router = APIRouter(tags=["apa-tables"])


def get_apa_table_service(db: Session = Depends(get_db)) -> ApaTableService:
    return ApaTableService(db)


@router.post("/api/v1/forms/{form_id}/apa-tables/generate", response_model=ApaTableRead)
def generate_apa_table(
    form_id: str,
    payload: ApaTableRequest,
    service: ApaTableService = Depends(get_apa_table_service),
) -> ApaTableRead:
    return service.generate_apa_table(form_id, payload)


@router.post("/api/v1/forms/{form_id}/apa-tables/batch", response_model=ApaTableBatchRead)
def generate_apa_tables_batch(
    form_id: str,
    payload: ApaTableBatchRequest,
    service: ApaTableService = Depends(get_apa_table_service),
) -> ApaTableBatchRead:
    return service.generate_apa_tables_batch(form_id, payload)


@router.post("/api/v1/forms/{form_id}/apa-tables/from-analysis-run/{analysis_run_id}", response_model=ApaTableBatchRead)
def generate_apa_tables_from_analysis_run(
    form_id: str,
    analysis_run_id: str,
    service: ApaTableService = Depends(get_apa_table_service),
) -> ApaTableBatchRead:
    return service.generate_from_analysis_run(
        form_id,
        analysis_run_id,
        decimals=3,
        include_discarded=False,
        score_aggregation="mean",
    )


@router.post("/api/v1/forms/{form_id}/apa-tables/from-orchestrated-run/{analysis_run_id}", response_model=ApaTableBatchRead)
def generate_apa_tables_from_orchestrated_run(
    form_id: str,
    analysis_run_id: str,
    service: ApaTableService = Depends(get_apa_table_service),
) -> ApaTableBatchRead:
    return service.generate_from_orchestrated_analysis(form_id, analysis_run_id, decimals=3)


@router.post("/api/v1/forms/{form_id}/apa-tables/export/markdown", response_model=ApaTableExportRead)
def export_apa_tables_markdown(
    form_id: str,
    payload: ApaTableBatchRequest,
    service: ApaTableService = Depends(get_apa_table_service),
) -> ApaTableExportRead:
    return service.export_apa_tables(form_id, payload, export_format="markdown")


@router.post("/api/v1/forms/{form_id}/apa-tables/export/html", response_model=ApaTableExportRead)
def export_apa_tables_html(
    form_id: str,
    payload: ApaTableBatchRequest,
    service: ApaTableService = Depends(get_apa_table_service),
) -> ApaTableExportRead:
    return service.export_apa_tables(form_id, payload, export_format="html")


@router.get("/api/v1/forms/{form_id}/apa-tables/options", response_model=ApaTableOptionsRead)
def get_apa_table_options(
    form_id: str,
    service: ApaTableService = Depends(get_apa_table_service),
) -> ApaTableOptionsRead:
    return service.list_apa_table_options(form_id)
