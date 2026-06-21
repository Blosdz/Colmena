from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FormQuestionBase(BaseModel):
    section_id: str | None = None
    instrument_id: str | None = None
    dimension_id: str | None = None
    project_variable_id: str | None = None
    code: str | None = Field(default=None, max_length=100)
    help_text: str | None = None
    question_type: str = Field(..., max_length=50)
    question_role: str = Field(default="item", max_length=50)
    measurement_level: str = Field(default="ordinal", max_length=50)
    data_type: str = Field(default="numeric", max_length=50)
    is_required: bool = False
    is_scored: bool = False
    is_reverse_scored: bool = False
    min_value: float | None = None
    max_value: float | None = None
    sort_order: int = Field(default=0, ge=0)
    validation_json: dict | list | None = None
    config_json: dict | list | None = None

    @field_validator("code", "help_text")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("question_type", "question_role", "measurement_level", "data_type")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must not be empty")
        return cleaned


class FormQuestionCreate(FormQuestionBase):
    label: str = Field(..., min_length=1)

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("label must not be empty")
        return cleaned


class FormQuestionUpdate(FormQuestionBase):
    label: str | None = Field(default=None, min_length=1)

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("label must not be empty")
        return cleaned


class FormQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    form_id: str
    section_id: str | None
    instrument_id: str | None
    dimension_id: str | None
    project_variable_id: str | None
    code: str | None
    label: str
    help_text: str | None
    question_type: str
    question_role: str
    measurement_level: str
    data_type: str
    is_required: bool
    is_scored: bool
    is_reverse_scored: bool
    min_value: float | None
    max_value: float | None
    sort_order: int
    validation_json: dict | list | None
    config_json: dict | list | None
    created_at: datetime
    updated_at: datetime


class FormQuestionListResponse(BaseModel):
    items: list[FormQuestionRead]
    total: int
