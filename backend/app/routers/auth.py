from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import AppThesisLinkRequest, AppThesisLinkResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/appthesis", response_model=AppThesisLinkResponse)
def link_appthesis(
    payload: AppThesisLinkRequest,
    service: AuthService = Depends(get_auth_service),
) -> AppThesisLinkResponse:
    """Vincula (o reutiliza) una cuenta de Colmena a partir de un JWT de AppThesis."""
    user, created = service.link_appthesis_account(payload.token)
    return AppThesisLinkResponse(ok=True, user=user, linked=not created)
