from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DatasetColumnRead(BaseModel):
    name: str
    label: str
    question_id: str | None = None
    kind: str


class DatasetRead(BaseModel):
    form_id: str
    mode: str
    total_rows: int
    total_columns: int
    columns: list[DatasetColumnRead]
    rows: list[dict[str, Any]]


class DataDictionaryItemRead(BaseModel):
    question_id: str
    column_name: str
    code: str | None
    label: str
    question_type: str
    question_role: str
    measurement_level: str
    data_type: str
    is_required: bool
    is_scored: bool
    is_reverse_scored: bool
    section_title: str | None
    instrument_name: str | None
    dimension_name: str | None
    project_variable_name: str | None
    options: list[dict[str, Any]]


class DataDictionaryRead(BaseModel):
    form_id: str
    items: list[DataDictionaryItemRead]


class CompletenessItemRead(BaseModel):
    question_id: str
    column_name: str
    label: str
    total_responses: int
    answered_count: int
    missing_count: int
    missing_percent: float
    required: bool
    warning_level: str


class CompletenessSummaryRead(BaseModel):
    form_id: str
    total_responses: int
    items: list[CompletenessItemRead]


class DatasetExportRequest(BaseModel):
    mode: str = Field(default="mixed")
    include_metadata: bool = True
    include_discarded: bool = False
    expand_multiple_choice: bool = False
    include_scores: bool = False


class DatasetExportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    form_id: str | None
    artifact_type: str
    file_name: str
    file_path: str
    mime_type: str | None
    file_size_bytes: int | None
    metadata_json: dict | list | None
    created_at: datetime


class DatasetExportListResponse(BaseModel):
    items: list[DatasetExportRead]
    total: int


class AnswerUpdateRequest(BaseModel):
    option_id: str | None = None
    value_text: str | None = None
    value_number: float | None = None
    value_date: datetime | None = None
    value_json: list[str] | list[dict] | dict | None = None

    @field_validator("value_text")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class AnswerUpdateRead(BaseModel):
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
    updated_at: datetime


class ResponseStatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in {"partial", "complete", "discarded"}:
            raise ValueError("status must be partial, complete, or discarded")
        return cleaned


class ResponseStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    response_id: str
    status: str
    updated_at: datetime
