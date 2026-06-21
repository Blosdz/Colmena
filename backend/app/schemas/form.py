from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FormBase(BaseModel):
    description: str | None = None
    instructions: str | None = None
    status: str = Field(default="draft", max_length=50)
    public_slug: str | None = Field(default=None, max_length=255)
    allow_anonymous: bool = True
    collect_started_at: datetime | None = None
    collect_closed_at: datetime | None = None
    thank_you_message: str | None = None
    metadata_json: str | None = None

    @field_validator("description", "instructions", "public_slug", "thank_you_message", "metadata_json")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("status must not be empty")
        return cleaned


class FormCreate(FormBase):
    title: str = Field(..., min_length=1, max_length=255)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be empty")
        return cleaned


class FormUpdate(FormBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be empty")
        return cleaned


class FormRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    description: str | None
    instructions: str | None
    status: str
    public_slug: str | None
    allow_anonymous: bool
    collect_started_at: datetime | None
    collect_closed_at: datetime | None
    thank_you_message: str | None
    metadata_json: str | None
    created_at: datetime
    updated_at: datetime


class FormListResponse(BaseModel):
    items: list[FormRead]
    total: int
