from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.descriptive import (
    CrosstabRead,
    DescriptiveOverviewRead,
    DescriptiveRunRead,
    DescriptiveRunRequest,
    DimensionDescriptiveListRead,
    FormDescriptiveReportRead,
    InstrumentDescriptiveListRead,
    ProjectVariableDescriptiveListRead,
    QuestionDescriptiveRead,
)
from app.schemas.scoring import ScoringResultsRead
from app.services.advanced_scoring_service import AdvancedScoringService
from app.services.descriptive_service import DescriptiveService


router = APIRouter(tags=["descriptives"])


def get_descriptive_service(db: Session = Depends(get_db)) -> DescriptiveService:
    return DescriptiveService(db)


def get_advanced_scoring_service(db: Session = Depends(get_db)) -> AdvancedScoringService:
    return AdvancedScoringService(db)


@router.get("/api/v1/forms/{form_id}/descriptives/overview", response_model=DescriptiveOverviewRead)
def get_descriptive_overview(
    form_id: str,
    include_discarded: bool = Query(default=False),
    service: DescriptiveService = Depends(get_descriptive_service),
) -> DescriptiveOverviewRead:
    return service.get_descriptive_overview(form_id, include_discarded=include_discarded)


@router.get("/api/v1/forms/{form_id}/descriptives", response_model=FormDescriptiveReportRead)
def get_form_descriptives(
    form_id: str,
    include_discarded: bool = Query(default=False),
    decimals: int = Query(default=3, ge=0, le=6),
    score_aggregation: str = Query(default="mean", pattern="^(sum|mean)$"),
    service: DescriptiveService = Depends(get_descriptive_service),
) -> FormDescriptiveReportRead:
    return service.get_form_descriptives(
        form_id,
        include_discarded=include_discarded,
        decimals=decimals,
        score_aggregation=score_aggregation,
    )


@router.get("/api/v1/forms/{form_id}/descriptives/scoring", response_model=ScoringResultsRead)
def get_scoring_descriptives(
    form_id: str,
    service: AdvancedScoringService = Depends(get_advanced_scoring_service),
) -> ScoringResultsRead:
    return service.get_form_score_results(form_id)


@router.get("/api/v1/forms/{form_id}/descriptives/questions/{question_id}", response_model=QuestionDescriptiveRead)
def get_question_descriptive(
    form_id: str,
    question_id: str,
    include_discarded: bool = Query(default=False),
    decimals: int = Query(default=3, ge=0, le=6),
    service: DescriptiveService = Depends(get_descriptive_service),
) -> QuestionDescriptiveRead:
    return service.get_question_descriptive(
        form_id,
        question_id,
        include_discarded=include_discarded,
        decimals=decimals,
    )


@router.get("/api/v1/forms/{form_id}/descriptives/dimensions", response_model=DimensionDescriptiveListRead)
def get_dimension_descriptives(
    form_id: str,
    include_discarded: bool = Query(default=False),
    decimals: int = Query(default=3, ge=0, le=6),
    score_aggregation: str = Query(default="mean", pattern="^(sum|mean)$"),
    service: DescriptiveService = Depends(get_descriptive_service),
) -> DimensionDescriptiveListRead:
    items = service.get_dimension_descriptives(
        form_id,
        include_discarded=include_discarded,
        decimals=decimals,
        score_aggregation=score_aggregation,
    )
    return DimensionDescriptiveListRead(form_id=form_id, aggregation=score_aggregation, items=items)


@router.get("/api/v1/forms/{form_id}/descriptives/instruments", response_model=InstrumentDescriptiveListRead)
def get_instrument_descriptives(
    form_id: str,
    include_discarded: bool = Query(default=False),
    decimals: int = Query(default=3, ge=0, le=6),
    score_aggregation: str = Query(default="mean", pattern="^(sum|mean)$"),
    service: DescriptiveService = Depends(get_descriptive_service),
) -> InstrumentDescriptiveListRead:
    items = service.get_instrument_descriptives(
        form_id,
        include_discarded=include_discarded,
        decimals=decimals,
        score_aggregation=score_aggregation,
    )
    return InstrumentDescriptiveListRead(form_id=form_id, aggregation=score_aggregation, items=items)


@router.get("/api/v1/forms/{form_id}/descriptives/project-variables", response_model=ProjectVariableDescriptiveListRead)
def get_project_variable_descriptives(
    form_id: str,
    include_discarded: bool = Query(default=False),
    decimals: int = Query(default=3, ge=0, le=6),
    service: DescriptiveService = Depends(get_descriptive_service),
) -> ProjectVariableDescriptiveListRead:
    items = service.get_project_variable_descriptives(
        form_id,
        include_discarded=include_discarded,
        decimals=decimals,
    )
    return ProjectVariableDescriptiveListRead(form_id=form_id, items=items)


@router.get("/api/v1/forms/{form_id}/descriptives/crosstab", response_model=CrosstabRead)
def get_crosstab(
    form_id: str,
    row_question_id: str,
    column_question_id: str,
    include_discarded: bool = Query(default=False),
    decimals: int = Query(default=3, ge=0, le=6),
    service: DescriptiveService = Depends(get_descriptive_service),
) -> CrosstabRead:
    return service.get_crosstab(
        form_id,
        row_question_id=row_question_id,
        column_question_id=column_question_id,
        include_discarded=include_discarded,
        decimals=decimals,
    )


@router.post("/api/v1/forms/{form_id}/descriptives/run", response_model=DescriptiveRunRead)
def run_descriptive_analysis(
    form_id: str,
    payload: DescriptiveRunRequest,
    service: DescriptiveService = Depends(get_descriptive_service),
) -> DescriptiveRunRead:
    return service.run_descriptive_analysis(form_id, payload)
