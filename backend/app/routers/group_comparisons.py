from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.group_comparison import (
    GroupComparisonOptionsRead,
    GroupComparisonRequest,
    GroupComparisonRunRead,
)
from app.services.group_comparison_service import GroupComparisonService


router = APIRouter(tags=["group-comparisons"])


def get_group_comparison_service(db: Session = Depends(get_db)) -> GroupComparisonService:
    return GroupComparisonService(db)


@router.post("/api/v1/forms/{form_id}/group-comparisons", response_model=GroupComparisonRunRead)
def run_group_comparison(
    form_id: str,
    payload: GroupComparisonRequest,
    service: GroupComparisonService = Depends(get_group_comparison_service),
) -> GroupComparisonRunRead:
    return service.run_group_comparison(form_id, payload)


@router.get("/api/v1/forms/{form_id}/group-comparisons/options", response_model=GroupComparisonOptionsRead)
def get_group_comparison_options(
    form_id: str,
    include_discarded: bool = Query(default=False),
    service: GroupComparisonService = Depends(get_group_comparison_service),
) -> GroupComparisonOptionsRead:
    return service.get_comparison_options(form_id, include_discarded=include_discarded)
