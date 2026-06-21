from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.statistical_decision import StatisticalDecisionRead, StatisticalDecisionRequest
from app.services.statistical_decision_service import StatisticalDecisionService


router = APIRouter(tags=["statistical-decisions"])


def get_statistical_decision_service(db: Session = Depends(get_db)) -> StatisticalDecisionService:
    return StatisticalDecisionService(db)


@router.post("/api/v1/forms/{form_id}/statistical-decision", response_model=StatisticalDecisionRead)
def get_statistical_decision(
    form_id: str,
    payload: StatisticalDecisionRequest,
    service: StatisticalDecisionService = Depends(get_statistical_decision_service),
) -> StatisticalDecisionRead:
    return service.make_decision(form_id, payload)
