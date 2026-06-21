from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FormAnswerCreate(BaseModel):
    question_id: str
    option_id: str | None = None
    value_text: str | None = None
    value_number: float | None = None
    value_date: datetime | None = None
    value_json: dict | list | None = None
    score_value: float | None = None

    @field_validator("value_text")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class FormAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    response_id: str
    question_id: str
    option_id: str | None
    value_text: str | None
    value_number: float | None
    value_date: datetime | None
    value_json: dict | list | None
    score_value: float | None
    created_at: datetime
    updated_at: datetime


class FormResponseBase(BaseModel):
    respondent_code: str | None = Field(default=None, max_length=100)
    status: str = Field(default="complete", max_length=50)
    submitted_at: datetime | None = None
    source: str = Field(default="internal", max_length=50)
    metadata_json: dict | list | None = None

    @field_validator("respondent_code")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("status", "source")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must not be empty")
        return cleaned


class FormResponseCreate(FormResponseBase):
    answers: list[FormAnswerCreate] = Field(default_factory=list)


class FormResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    form_id: str
    respondent_code: str | None
    status: str
    submitted_at: datetime | None
    source: str
    metadata_json: dict | list | None
    created_at: datetime
    updated_at: datetime
    answers: list[FormAnswerRead]


class FormResponseListResponse(BaseModel):
    items: list[FormResponseRead]
    total: int
