from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.correlation import (
    CorrelationMatrixRead,
    CorrelationMatrixRequest,
    CorrelationRunRead,
    CorrelationRequest,
)
from app.services.correlation_service import CorrelationService


router = APIRouter(tags=["correlations"])


def get_correlation_service(db: Session = Depends(get_db)) -> CorrelationService:
    return CorrelationService(db)


@router.post("/api/v1/forms/{form_id}/correlations/pair", response_model=CorrelationRunRead)
def run_pair_correlation(
    form_id: str,
    payload: CorrelationRequest,
    service: CorrelationService = Depends(get_correlation_service),
) -> CorrelationRunRead:
    return service.run_pair_correlation(form_id, payload)


@router.post("/api/v1/forms/{form_id}/correlations/matrix", response_model=CorrelationMatrixRead)
def run_correlation_matrix(
    form_id: str,
    payload: CorrelationMatrixRequest,
    service: CorrelationService = Depends(get_correlation_service),
) -> CorrelationMatrixRead:
    return service.run_correlation_matrix(form_id, payload)


@router.get(
    "/api/v1/forms/{form_id}/correlations/instruments/{instrument_id}/dimensions",
    response_model=CorrelationMatrixRead,
)
def get_instrument_dimensions_correlations(
    form_id: str,
    instrument_id: str,
    method: str = Query(default="auto", pattern="^(auto|pearson|spearman|kendall)$"),
    alpha: float = Query(default=0.05, ge=0.001, le=0.20),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    score_aggregation: str = Query(default="mean", pattern="^(sum|mean)$"),
    service: CorrelationService = Depends(get_correlation_service),
) -> CorrelationMatrixRead:
    return service.get_instrument_dimension_matrix(
        form_id,
        instrument_id,
        method=method,
        alpha=alpha,
        decimals=decimals,
        include_discarded=include_discarded,
        score_aggregation=score_aggregation,
    )


@router.get("/api/v1/forms/{form_id}/correlations/instruments", response_model=CorrelationMatrixRead)
def get_instruments_correlations(
    form_id: str,
    method: str = Query(default="auto", pattern="^(auto|pearson|spearman|kendall)$"),
    alpha: float = Query(default=0.05, ge=0.001, le=0.20),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    score_aggregation: str = Query(default="mean", pattern="^(sum|mean)$"),
    service: CorrelationService = Depends(get_correlation_service),
) -> CorrelationMatrixRead:
    return service.get_instruments_matrix(
        form_id,
        method=method,
        alpha=alpha,
        decimals=decimals,
        include_discarded=include_discarded,
        score_aggregation=score_aggregation,
    )


@router.get("/api/v1/forms/{form_id}/correlations/project-variables", response_model=CorrelationMatrixRead)
def get_project_variables_correlations(
    form_id: str,
    method: str = Query(default="auto", pattern="^(auto|pearson|spearman|kendall)$"),
    alpha: float = Query(default=0.05, ge=0.001, le=0.20),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    score_aggregation: str = Query(default="mean", pattern="^(sum|mean)$"),
    service: CorrelationService = Depends(get_correlation_service),
) -> CorrelationMatrixRead:
    return service.get_project_variables_matrix(
        form_id,
        method=method,
        alpha=alpha,
        decimals=decimals,
        include_discarded=include_discarded,
        score_aggregation=score_aggregation,
    )
