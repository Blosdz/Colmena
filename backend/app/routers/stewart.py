from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.stewart import StewartMatrixRead
from app.services.stewart_service import StewartService

router = APIRouter(tags=["stewart"])


def get_stewart_service(db: Session = Depends(get_db)) -> StewartService:
    return StewartService(db)


@router.get("/api/v1/forms/{form_id}/descriptives/stewart", response_model=StewartMatrixRead)
def get_stewart_matrix(
    form_id: str,
    instrument_id: str | None = Query(default=None),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    score_aggregation: str = Query(default="sum", pattern="^(sum|mean)$"),
    service: StewartService = Depends(get_stewart_service),
) -> StewartMatrixRead:
    return service.get_stewart_matrix(
        form_id,
        instrument_id=instrument_id,
        include_discarded=include_discarded,
        decimals=decimals,
        score_aggregation=score_aggregation,
    )
