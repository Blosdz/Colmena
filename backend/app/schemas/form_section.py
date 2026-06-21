from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FormSectionBase(BaseModel):
    description: str | None = None
    sort_order: int = Field(default=0, ge=0)

    @field_validator("description")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class FormSectionCreate(FormSectionBase):
    title: str = Field(..., min_length=1, max_length=255)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be empty")
        return cleaned


class FormSectionUpdate(FormSectionBase):
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


class FormSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    form_id: str
    title: str
    description: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class FormSectionListResponse(BaseModel):
    items: list[FormSectionRead]
    total: int
