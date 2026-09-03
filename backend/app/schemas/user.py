from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AppThesisLinkRequest(BaseModel):
    """Token JWT emitido por thesis-backend (AppThesis) para vincular la cuenta."""

    token: str = Field(..., min_length=10)


class RegisterRequest(BaseModel):
    """Alta de una cuenta standalone de Colmena."""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=8, max_length=128)


class PasswordResetRequestResponse(BaseModel):
    ok: bool = True
    # Solo en desarrollo (sin envío de correo): enlace directo para continuar.
    reset_url: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    username: str
    email: str
    status: str
    appthesis_user_id: str | None
    thesis_id: str | None
    created_at: datetime
    updated_at: datetime


class AuthTokenResponse(BaseModel):
    ok: bool = True
    token: str
    user: UserRead


class AppThesisLinkResponse(BaseModel):
    ok: bool = True
    user: UserRead
    linked: bool = True
