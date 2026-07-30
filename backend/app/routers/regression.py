from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.regression import RegressionRequest, RegressionRunRead
from app.services.regression_service import RegressionService

router = APIRouter(tags=["regression"])


def get_regression_service(db: Session = Depends(get_db)) -> RegressionService:
    return RegressionService(db)


@router.post("/api/v1/forms/{form_id}/regression/run", response_model=RegressionRunRead)
def run_regression(
    form_id: str,
    payload: RegressionRequest,
    service: RegressionService = Depends(get_regression_service),
) -> RegressionRunRead:
    return service.run_regression(form_id, payload)
