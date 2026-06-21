from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.form_response import FormResponseCreate, FormResponseListResponse, FormResponseRead
from app.services.response_service import ResponseService

router = APIRouter(tags=["responses"])


def get_response_service(db: Session = Depends(get_db)) -> ResponseService:
    return ResponseService(db)


@router.post("/api/v1/forms/{form_id}/responses", response_model=FormResponseRead, status_code=201)
def create_response(
    form_id: str,
    payload: FormResponseCreate,
    service: ResponseService = Depends(get_response_service),
) -> FormResponseRead:
    return service.create_response(form_id, payload)


@router.get("/api/v1/forms/{form_id}/responses", response_model=FormResponseListResponse)
def list_responses(
    form_id: str,
    service: ResponseService = Depends(get_response_service),
) -> FormResponseListResponse:
    items, total = service.list_responses(form_id)
    return FormResponseListResponse(items=items, total=total)


@router.get("/api/v1/form-responses/{response_id}", response_model=FormResponseRead)
def get_response(
    response_id: str,
    service: ResponseService = Depends(get_response_service),
) -> FormResponseRead:
    return service.get_response(response_id)
