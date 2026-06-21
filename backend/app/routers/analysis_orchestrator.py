from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analysis_orchestrator import (
    AnalysisOptionsRead,
    AnalysisSummaryRead,
    FullScanRequest,
    OrchestratedAnalysisRead,
    OrchestratedAnalysisRequest,
)
from app.services.analysis_orchestrator_service import AnalysisOrchestratorService


router = APIRouter(tags=["analysis-orchestrator"])


def get_analysis_orchestrator_service(db: Session = Depends(get_db)) -> AnalysisOrchestratorService:
    return AnalysisOrchestratorService(db)


@router.post("/api/v1/forms/{form_id}/analysis/run", response_model=OrchestratedAnalysisRead)
def run_analysis(
    form_id: str,
    payload: OrchestratedAnalysisRequest,
    service: AnalysisOrchestratorService = Depends(get_analysis_orchestrator_service),
) -> OrchestratedAnalysisRead:
    return service.run_orchestrated_analysis(form_id, payload)


@router.get("/api/v1/forms/{form_id}/analysis/options", response_model=AnalysisOptionsRead)
def get_analysis_options(
    form_id: str,
    service: AnalysisOrchestratorService = Depends(get_analysis_orchestrator_service),
) -> AnalysisOptionsRead:
    return service.list_analysis_options(form_id)


@router.post("/api/v1/forms/{form_id}/analysis/full-scan", response_model=OrchestratedAnalysisRead)
def run_full_scan(
    form_id: str,
    payload: FullScanRequest,
    service: AnalysisOrchestratorService = Depends(get_analysis_orchestrator_service),
) -> OrchestratedAnalysisRead:
    form = service._get_form(form_id)
    result = service.run_full_form_scan(form, payload)
    if payload.store_result:
        analysis_run = service.store_orchestrated_analysis_run(form, payload.model_dump(), result)
        result.analysis_run_id = analysis_run.id
    return result


@router.get("/api/v1/forms/{form_id}/analysis/summary", response_model=AnalysisSummaryRead)
def get_analysis_summary(
    form_id: str,
    service: AnalysisOrchestratorService = Depends(get_analysis_orchestrator_service),
) -> AnalysisSummaryRead:
    return service.get_analysis_summary(form_id)
