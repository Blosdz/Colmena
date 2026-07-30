from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reliability import (
    CompositeReliabilityReportRead,
    CompositeReliabilityTargetRead,
    ReliabilityReportRead,
    ReliabilityRunRead,
    ReliabilityRunRequest,
    ReliabilityTargetRead,
)
from app.services.reliability_service import ReliabilityService


router = APIRouter(tags=["reliability"])


def get_reliability_service(db: Session = Depends(get_db)) -> ReliabilityService:
    return ReliabilityService(db)


@router.get("/api/v1/forms/{form_id}/reliability", response_model=ReliabilityReportRead)
def get_reliability_report(
    form_id: str,
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    service: ReliabilityService = Depends(get_reliability_service),
) -> ReliabilityReportRead:
    return service.get_reliability_report(
        form_id,
        decimals=decimals,
        include_discarded=include_discarded,
    )


@router.get("/api/v1/forms/{form_id}/reliability/instruments", response_model=ReliabilityReportRead)
def get_instruments_reliability(
    form_id: str,
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    service: ReliabilityService = Depends(get_reliability_service),
) -> ReliabilityReportRead:
    full = service.get_reliability_report(form_id, decimals=decimals, include_discarded=include_discarded)
    results = [item for item in full.results if item.target_type == "instrument"]
    return full.model_copy(
        update={
            "results": results,
            "total_targets": len(results),
            "applicable_targets": sum(1 for item in results if item.result.classification != "not_applicable"),
        }
    )


@router.get("/api/v1/forms/{form_id}/reliability/dimensions", response_model=ReliabilityReportRead)
def get_dimensions_reliability(
    form_id: str,
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    service: ReliabilityService = Depends(get_reliability_service),
) -> ReliabilityReportRead:
    full = service.get_reliability_report(form_id, decimals=decimals, include_discarded=include_discarded)
    results = [item for item in full.results if item.target_type == "dimension"]
    return full.model_copy(
        update={
            "results": results,
            "total_targets": len(results),
            "applicable_targets": sum(1 for item in results if item.result.classification != "not_applicable"),
        }
    )


@router.get("/api/v1/forms/{form_id}/reliability/instruments/{instrument_id}", response_model=ReliabilityTargetRead)
def get_instrument_reliability(
    form_id: str,
    instrument_id: str,
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    service: ReliabilityService = Depends(get_reliability_service),
) -> ReliabilityTargetRead:
    return service.get_instrument_reliability(
        form_id,
        instrument_id,
        decimals=decimals,
        include_discarded=include_discarded,
    )


@router.get("/api/v1/forms/{form_id}/reliability/dimensions/{dimension_id}", response_model=ReliabilityTargetRead)
def get_dimension_reliability(
    form_id: str,
    dimension_id: str,
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    service: ReliabilityService = Depends(get_reliability_service),
) -> ReliabilityTargetRead:
    return service.get_dimension_reliability(
        form_id,
        dimension_id,
        decimals=decimals,
        include_discarded=include_discarded,
    )


@router.get(
    "/api/v1/forms/{form_id}/reliability/composite/dimensions",
    response_model=CompositeReliabilityReportRead,
)
def get_composite_dimensions_reliability(
    form_id: str,
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    service: ReliabilityService = Depends(get_reliability_service),
) -> CompositeReliabilityReportRead:
    full = service.get_composite_reliability_report(form_id, decimals=decimals, include_discarded=include_discarded)
    results = [item for item in full.results if item.target_type == "dimension"]
    return full.model_copy(
        update={
            "results": results,
            "total_targets": len(results),
            "applicable_targets": sum(1 for item in results if item.result.classification != "not_applicable"),
        }
    )


@router.get(
    "/api/v1/forms/{form_id}/reliability/composite/instruments/{instrument_id}",
    response_model=CompositeReliabilityTargetRead,
)
def get_composite_instrument_reliability(
    form_id: str,
    instrument_id: str,
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    service: ReliabilityService = Depends(get_reliability_service),
) -> CompositeReliabilityTargetRead:
    return service.get_instrument_composite_reliability(
        form_id,
        instrument_id,
        decimals=decimals,
        include_discarded=include_discarded,
    )


@router.get(
    "/api/v1/forms/{form_id}/reliability/composite/dimensions/{dimension_id}",
    response_model=CompositeReliabilityTargetRead,
)
def get_composite_dimension_reliability(
    form_id: str,
    dimension_id: str,
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    service: ReliabilityService = Depends(get_reliability_service),
) -> CompositeReliabilityTargetRead:
    return service.get_dimension_composite_reliability(
        form_id,
        dimension_id,
        decimals=decimals,
        include_discarded=include_discarded,
    )


@router.post("/api/v1/forms/{form_id}/reliability/run", response_model=ReliabilityRunRead)
def run_reliability(
    form_id: str,
    payload: ReliabilityRunRequest,
    service: ReliabilityService = Depends(get_reliability_service),
) -> ReliabilityRunRead:
    return service.run_reliability_analysis(form_id, payload)
