from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.word_report import WordReportGenerateRequest, WordReportOptionsRead, WordReportRead
from app.services.word_report_service import WordReportService


router = APIRouter(tags=["word-reports"])


def get_word_report_service(db: Session = Depends(get_db)) -> WordReportService:
    return WordReportService(db)


@router.post("/api/v1/forms/{form_id}/word-reports/generate", response_model=WordReportRead)
def generate_word_report(
    form_id: str,
    payload: WordReportGenerateRequest,
    service: WordReportService = Depends(get_word_report_service),
) -> WordReportRead:
    return service.generate_word_report(form_id, payload)


@router.post("/api/v1/forms/{form_id}/word-reports/from-analysis-run/{analysis_run_id}", response_model=WordReportRead)
def generate_word_report_from_analysis_run(
    form_id: str,
    analysis_run_id: str,
    service: WordReportService = Depends(get_word_report_service),
) -> WordReportRead:
    return service.generate_from_analysis_run_report(form_id, analysis_run_id)


@router.post("/api/v1/forms/{form_id}/word-reports/from-orchestrated-run/{analysis_run_id}", response_model=WordReportRead)
def generate_word_report_from_orchestrated_run(
    form_id: str,
    analysis_run_id: str,
    service: WordReportService = Depends(get_word_report_service),
) -> WordReportRead:
    return service.generate_from_orchestrated_run_report(form_id, analysis_run_id)


@router.get("/api/v1/forms/{form_id}/word-reports/options", response_model=WordReportOptionsRead)
def get_word_report_options(
    form_id: str,
    service: WordReportService = Depends(get_word_report_service),
) -> WordReportOptionsRead:
    return service.get_word_report_options(form_id)


@router.get("/api/v1/forms/{form_id}/word-reports", response_model=list[WordReportRead])
def list_word_reports(
    form_id: str,
    service: WordReportService = Depends(get_word_report_service),
) -> list[WordReportRead]:
    return service.list_word_reports(form_id)
