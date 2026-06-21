from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


TABLE_TYPES = {
    "frequencies",
    "descriptives",
    "normality",
    "correlation",
    "correlation_matrix",
    "group_comparison",
    "categorical_association",
    "scoring_summary",
    "score_band_distribution",
    "control_scale_flags",
    "orchestrated_summary",
}
SOURCE_TYPES = {"live", "analysis_run", "orchestrated"}
EXPORT_FORMATS = {"markdown", "html", "json"}


class ApaTableCellRead(BaseModel):
    value: str
    raw_value: Any | None = None
    align: str = "left"
    format_type: str | None = None

    @field_validator("align")
    @classmethod
    def validate_align(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"left", "center", "right"}:
            raise ValueError("align must be left, center, or right")
        return cleaned

    @field_validator("format_type")
    @classmethod
    def validate_format_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in {"text", "integer", "decimal", "p_value", "percentage", "statistic"}:
            raise ValueError("invalid format_type")
        return cleaned


class ApaTableColumnRead(BaseModel):
    key: str
    label: str
    align: str = "left"
    format_type: str | None = None

    @field_validator("align")
    @classmethod
    def validate_align(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"left", "center", "right"}:
            raise ValueError("align must be left, center, or right")
        return cleaned

    @field_validator("format_type")
    @classmethod
    def validate_format_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in {"text", "integer", "decimal", "p_value", "percentage", "statistic"}:
            raise ValueError("invalid format_type")
        return cleaned


class ApaTableRowRead(BaseModel):
    cells: list[ApaTableCellRead]
    row_type: str = "body"

    @field_validator("row_type")
    @classmethod
    def validate_row_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"body", "subtotal", "total", "note"}:
            raise ValueError("invalid row_type")
        return cleaned


class ApaTableNoteRead(BaseModel):
    note_type: str = "general"
    text: str

    @field_validator("note_type")
    @classmethod
    def validate_note_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"general", "statistical", "caution", "source"}:
            raise ValueError("invalid note_type")
        return cleaned


class ApaTableRead(BaseModel):
    table_id: str
    table_number: int | None = None
    table_type: str
    title: str
    subtitle: str | None = None
    columns: list[ApaTableColumnRead]
    rows: list[ApaTableRowRead]
    notes: list[ApaTableNoteRead]
    markdown: str
    html: str
    ready_for_word: bool
    ready_for_frontend: bool
    warnings: list[str]
    source: dict[str, Any] | None = None

    @field_validator("table_type")
    @classmethod
    def validate_table_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in TABLE_TYPES:
            raise ValueError("invalid table_type")
        return cleaned


class ApaTableRequest(BaseModel):
    table_type: str
    source_type: str = "live"
    form_id: str | None = None
    analysis_run_id: str | None = None
    target_ids: list[str] | None = None
    options: dict[str, Any] | None = None
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = "mean"

    @field_validator("table_type")
    @classmethod
    def validate_table_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in TABLE_TYPES:
            raise ValueError("invalid table_type")
        return cleaned

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in SOURCE_TYPES:
            raise ValueError("invalid source_type")
        return cleaned

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"mean", "sum"}:
            raise ValueError("score_aggregation must be mean or sum")
        return cleaned


class ApaTableBatchRequest(BaseModel):
    form_id: str
    table_types: list[str]
    analysis_run_ids: list[str] | None = None
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = "mean"
    options: dict[str, Any] | None = None

    @field_validator("table_types")
    @classmethod
    def validate_table_types(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("table_types must not be empty")
        cleaned_values: list[str] = []
        for item in value:
            cleaned = item.strip().lower()
            if cleaned not in TABLE_TYPES:
                raise ValueError("invalid table_type in batch")
            cleaned_values.append(cleaned)
        return cleaned_values

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"mean", "sum"}:
            raise ValueError("score_aggregation must be mean or sum")
        return cleaned


class ApaTableBatchRead(BaseModel):
    form_id: str
    project_id: str
    total_tables: int
    tables: list[ApaTableRead]
    warnings: list[str]


class ApaTableExportRequest(BaseModel):
    format: str
    table_type: str | None = None
    analysis_run_id: str | None = None
    decimals: int = Field(default=3, ge=0, le=6)

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in EXPORT_FORMATS:
            raise ValueError("invalid export format")
        return cleaned

    @field_validator("table_type")
    @classmethod
    def validate_table_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in TABLE_TYPES:
            raise ValueError("invalid table_type")
        return cleaned


class ApaTableExportRead(BaseModel):
    artifact_id: str | None
    file_name: str
    file_path: str
    mime_type: str
    table_count: int
    created_at: datetime


class CompatibleAnalysisRunRead(BaseModel):
    id: str
    analysis_type: str
    created_at: datetime


class ApaTableRecommendationRead(BaseModel):
    table_type: str
    reason: str


class ApaTableOptionsRead(BaseModel):
    form_id: str
    table_types: list[str]
    analysis_runs: list[CompatibleAnalysisRunRead]
    recommendations: list[ApaTableRecommendationRead]
