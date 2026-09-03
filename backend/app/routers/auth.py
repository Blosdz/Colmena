from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.user import (
    AppThesisLinkRequest,
    AppThesisLinkResponse,
    AuthTokenResponse,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RegisterRequest,
)
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


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    """Alta de una cuenta standalone de Colmena (email + contraseña)."""
    user, token = service.register_local(payload.name, payload.email, payload.password)
    return AuthTokenResponse(token=token, user=user)


@router.post("/login", response_model=AuthTokenResponse)
def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    """Inicio de sesión con una cuenta standalone de Colmena."""
    user, token = service.login_local(payload.email, payload.password)
    return AuthTokenResponse(token=token, user=user)


@router.post("/password/reset-request", response_model=PasswordResetRequestResponse)
def request_password_reset(
    payload: PasswordResetRequest,
    service: AuthService = Depends(get_auth_service),
) -> PasswordResetRequestResponse:
    """Pide un enlace para restablecer la contraseña.

    Responde siempre igual exista o no la cuenta. En desarrollo devuelve el
    enlace directamente (no hay servicio de correo).
    """
    reset_url = service.request_password_reset(payload.email)
    expose = reset_url if get_settings().environment == "development" else None
    return PasswordResetRequestResponse(ok=True, reset_url=expose)


@router.post("/password/reset", response_model=AuthTokenResponse)
def reset_password(
    payload: PasswordResetConfirm,
    service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    """Fija una nueva contraseña a partir del token del enlace y deja la sesión iniciada."""
    user, token = service.reset_password(payload.token, payload.password)
    return AuthTokenResponse(token=token, user=user)
