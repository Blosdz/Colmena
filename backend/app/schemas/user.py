from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppThesisLinkRequest(BaseModel):
    """Token JWT emitido por thesis-backend (AppThesis) para vincular la cuenta."""

    token: str = Field(..., min_length=10)


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


class AppThesisLinkResponse(BaseModel):
    ok: bool = True
    user: UserRead
    linked: bool = True
