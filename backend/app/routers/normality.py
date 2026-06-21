from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.normality import NormalityReportRead, NormalityRunRead, NormalityRunRequest, NormalityTestResultRead
from app.services.normality_service import NormalityService


router = APIRouter(tags=["normality"])


def get_normality_service(db: Session = Depends(get_db)) -> NormalityService:
    return NormalityService(db)


@router.get("/api/v1/forms/{form_id}/normality", response_model=NormalityReportRead)
def get_normality_report(
    form_id: str,
    method: str = Query(default="auto", pattern="^(auto|shapiro|lilliefors|dagostino)$"),
    alpha: float = Query(default=0.05, ge=0.001, le=0.20),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    score_aggregation: str = Query(default="mean", pattern="^(sum|mean)$"),
    service: NormalityService = Depends(get_normality_service),
) -> NormalityReportRead:
    return service.get_normality_report(
        form_id,
        method=method,
        alpha=alpha,
        decimals=decimals,
        include_discarded=include_discarded,
        score_aggregation=score_aggregation,
    )


@router.get("/api/v1/forms/{form_id}/normality/questions/{question_id}", response_model=NormalityTestResultRead)
def get_question_normality(
    form_id: str,
    question_id: str,
    method: str = Query(default="auto", pattern="^(auto|shapiro|lilliefors|dagostino)$"),
    alpha: float = Query(default=0.05, ge=0.001, le=0.20),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    service: NormalityService = Depends(get_normality_service),
) -> NormalityTestResultRead:
    return service.get_question_normality(
        form_id,
        question_id,
        method=method,
        alpha=alpha,
        decimals=decimals,
        include_discarded=include_discarded,
    )


@router.get("/api/v1/forms/{form_id}/normality/dimensions", response_model=NormalityReportRead)
def get_dimensions_normality(
    form_id: str,
    method: str = Query(default="auto", pattern="^(auto|shapiro|lilliefors|dagostino)$"),
    alpha: float = Query(default=0.05, ge=0.001, le=0.20),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    score_aggregation: str = Query(default="mean", pattern="^(sum|mean)$"),
    service: NormalityService = Depends(get_normality_service),
) -> NormalityReportRead:
    full = service.get_normality_report(
        form_id,
        method=method,
        alpha=alpha,
        decimals=decimals,
        include_discarded=include_discarded,
        score_aggregation=score_aggregation,
    )
    results = [item for item in full.results if item.target_type == "dimension"]
    return full.model_copy(update={"results": results, "total_targets": len(results), "applicable_targets": sum(1 for item in results if item.classification in {'normal','non_normal','inconclusive'}), "normal_count": sum(1 for item in results if item.classification == 'normal'), "non_normal_count": sum(1 for item in results if item.classification == 'non_normal'), "inconclusive_count": sum(1 for item in results if item.classification == 'inconclusive'), "not_applicable_count": sum(1 for item in results if item.classification == 'not_applicable')})


@router.get("/api/v1/forms/{form_id}/normality/instruments", response_model=NormalityReportRead)
def get_instruments_normality(
    form_id: str,
    method: str = Query(default="auto", pattern="^(auto|shapiro|lilliefors|dagostino)$"),
    alpha: float = Query(default=0.05, ge=0.001, le=0.20),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    score_aggregation: str = Query(default="mean", pattern="^(sum|mean)$"),
    service: NormalityService = Depends(get_normality_service),
) -> NormalityReportRead:
    full = service.get_normality_report(
        form_id,
        method=method,
        alpha=alpha,
        decimals=decimals,
        include_discarded=include_discarded,
        score_aggregation=score_aggregation,
    )
    results = [item for item in full.results if item.target_type == "instrument"]
    return full.model_copy(update={"results": results, "total_targets": len(results), "applicable_targets": sum(1 for item in results if item.classification in {'normal','non_normal','inconclusive'}), "normal_count": sum(1 for item in results if item.classification == 'normal'), "non_normal_count": sum(1 for item in results if item.classification == 'non_normal'), "inconclusive_count": sum(1 for item in results if item.classification == 'inconclusive'), "not_applicable_count": sum(1 for item in results if item.classification == 'not_applicable')})


@router.get("/api/v1/forms/{form_id}/normality/project-variables", response_model=NormalityReportRead)
def get_project_variables_normality(
    form_id: str,
    method: str = Query(default="auto", pattern="^(auto|shapiro|lilliefors|dagostino)$"),
    alpha: float = Query(default=0.05, ge=0.001, le=0.20),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    score_aggregation: str = Query(default="mean", pattern="^(sum|mean)$"),
    service: NormalityService = Depends(get_normality_service),
) -> NormalityReportRead:
    full = service.get_normality_report(
        form_id,
        method=method,
        alpha=alpha,
        decimals=decimals,
        include_discarded=include_discarded,
        score_aggregation=score_aggregation,
    )
    results = [item for item in full.results if item.target_type == "project_variable"]
    return full.model_copy(update={"results": results, "total_targets": len(results), "applicable_targets": sum(1 for item in results if item.classification in {'normal','non_normal','inconclusive'}), "normal_count": sum(1 for item in results if item.classification == 'normal'), "non_normal_count": sum(1 for item in results if item.classification == 'non_normal'), "inconclusive_count": sum(1 for item in results if item.classification == 'inconclusive'), "not_applicable_count": sum(1 for item in results if item.classification == 'not_applicable')})


@router.post("/api/v1/forms/{form_id}/normality/run", response_model=NormalityRunRead)
def run_normality(
    form_id: str,
    payload: NormalityRunRequest,
    service: NormalityService = Depends(get_normality_service),
) -> NormalityRunRead:
    return service.run_normality_analysis(form_id, payload)
