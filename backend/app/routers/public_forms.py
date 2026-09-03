from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.public_form import PublicFormRead, PublicFormResponseCreate, PublicFormResponseRead
from app.services.public_form_service import PublicFormService

router = APIRouter(prefix="/api/public/forms", tags=["public-forms"])


def get_public_form_service(db: Session = Depends(get_db)) -> PublicFormService:
    return PublicFormService(db)


@router.get("/{public_slug}", response_model=PublicFormRead)
def get_public_form(
    public_slug: str,
    service: PublicFormService = Depends(get_public_form_service),
) -> PublicFormRead:
    return service.get_public_form_by_slug(public_slug)


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.client.host if request.client else None


@router.post("/{public_slug}/responses", response_model=PublicFormResponseRead, status_code=201)
def submit_public_response(
    public_slug: str,
    payload: PublicFormResponseCreate,
    request: Request,
    service: PublicFormService = Depends(get_public_form_service),
) -> PublicFormResponseRead:
    return service.submit_public_response(public_slug, payload, client_ip=_client_ip(request))
