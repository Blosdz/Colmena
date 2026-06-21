from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FormDimensionBase(BaseModel):
    code: str | None = Field(default=None, max_length=100)
    description: str | None = None
    sort_order: int = Field(default=0, ge=0)

    @field_validator("code", "description")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class FormDimensionCreate(FormDimensionBase):
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class FormDimensionUpdate(FormDimensionBase):
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


class FormDimensionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    instrument_id: str
    name: str
    code: str | None
    description: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class FormDimensionListResponse(BaseModel):
    items: list[FormDimensionRead]
    total: int
