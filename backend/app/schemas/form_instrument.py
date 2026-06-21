from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FormInstrumentBase(BaseModel):
    project_variable_id: str | None = None
    acronym: str | None = Field(default=None, max_length=50)
    author: str | None = Field(default=None, max_length=255)
    year: int | None = Field(default=None, ge=0, le=3000)
    description: str | None = None
    response_scale_name: str | None = Field(default=None, max_length=255)
    scoring_method: str | None = Field(default=None, max_length=255)
    reverse_scoring_enabled: bool = False
    sort_order: int = Field(default=0, ge=0)

    @field_validator("acronym", "author", "description", "response_scale_name", "scoring_method")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class FormInstrumentCreate(FormInstrumentBase):
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class FormInstrumentUpdate(FormInstrumentBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class FormInstrumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    form_id: str
    project_variable_id: str | None
    name: str
    acronym: str | None
    author: str | None
    year: int | None
    description: str | None
    response_scale_name: str | None
    scoring_method: str | None
    reverse_scoring_enabled: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class FormInstrumentListResponse(BaseModel):
    items: list[FormInstrumentRead]
    total: int
