from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FormQuestionOptionBase(BaseModel):
    value: str = Field(..., min_length=1, max_length=255)
    score: float | None = None
    sort_order: int = Field(default=0, ge=0)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be empty")
        return cleaned


class FormQuestionOptionCreate(FormQuestionOptionBase):
    label: str = Field(..., min_length=1, max_length=255)

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("label must not be empty")
        return cleaned


class FormQuestionOptionUpdate(FormQuestionOptionBase):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    value: str | None = Field(default=None, min_length=1, max_length=255)
    score: float | None = None
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("label", "value")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("text field must not be empty")
        return cleaned


class FormQuestionOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    label: str
    value: str
    score: float | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class FormQuestionOptionListResponse(BaseModel):
    items: list[FormQuestionOptionRead]
    total: int
