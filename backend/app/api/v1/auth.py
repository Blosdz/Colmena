from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.services.appthesis_auth import AppThesisAuthService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer(auto_error=True)


class AppThesisLinkResponse(BaseModel):
    ok: bool = True
    linked: bool
    user: UserRead


@router.post("/register", response_model=UserRead, status_code=201)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_db)):
    service = AuthService(session)
    user = await service.register(payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db)):
    service = AuthService(session)
    token = await service.login(payload)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user)


@router.post("/appthesis", response_model=AppThesisLinkResponse)
async def link_appthesis(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
):
    """Vincula (o reutiliza) una cuenta de COLMENA a partir de un JWT de AppThesis.

    Lo llama el callback SSO del frontend (`/auth/callback?token=`). Tras esto, el
    mismo JWT sirve como `Authorization: Bearer` en el resto de `/api/v1/*`.
    """
    user, created = await AppThesisAuthService(session).link_account(credentials.credentials)
    return AppThesisLinkResponse(linked=not created, user=UserRead.model_validate(user))
