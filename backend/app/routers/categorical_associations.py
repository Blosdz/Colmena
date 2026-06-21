from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.categorical_association import (
    CategoricalAssociationOptionsRead,
    CategoricalAssociationRequest,
    CategoricalAssociationRunRead,
)
from app.services.categorical_association_service import CategoricalAssociationService


router = APIRouter(tags=["categorical-associations"])


def get_categorical_association_service(db: Session = Depends(get_db)) -> CategoricalAssociationService:
    return CategoricalAssociationService(db)


@router.post("/api/v1/forms/{form_id}/categorical-associations", response_model=CategoricalAssociationRunRead)
def run_categorical_association(
    form_id: str,
    payload: CategoricalAssociationRequest,
    service: CategoricalAssociationService = Depends(get_categorical_association_service),
) -> CategoricalAssociationRunRead:
    return service.run_categorical_association(form_id, payload)


@router.get(
    "/api/v1/forms/{form_id}/categorical-associations/options",
    response_model=CategoricalAssociationOptionsRead,
)
def get_categorical_association_options(
    form_id: str,
    include_discarded: bool = Query(default=False),
    service: CategoricalAssociationService = Depends(get_categorical_association_service),
) -> CategoricalAssociationOptionsRead:
    return service.list_categorical_association_options(form_id, include_discarded=include_discarded)
