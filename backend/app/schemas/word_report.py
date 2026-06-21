from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


REPORT_TYPES = {"descriptive_report", "inferential_report", "orchestrated_report", "full_form_report"}
SOURCE_TYPES = {"live", "analysis_run", "orchestrated", "mixed"}
CHART_IMAGE_MODES = {"placeholders_only", "images_if_available", "selected_images_only"}


class WordReportSectionRead(BaseModel):
    section_key: str
    title: str
    included: bool
    summary: str
    warnings: list[str]


class WordReportGenerateRequest(BaseModel):
    report_type: str
    source_type: str
    analysis_run_ids: list[str] | None = None
    orchestrated_analysis_run_id: str | None = None
    title: str | None = None
    subtitle: str | None = None
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = "mean"
    include_charts_placeholders: bool = True
    include_chart_images: bool = True
    chart_image_artifact_ids: list[str] | None = None
    chart_image_mode: str = "images_if_available"
    include_plain_language_explanations: bool = True
    include_technical_appendix: bool = False
    include_cover: bool = True
    include_methodology_summary: bool = True
    options: dict[str, Any] | None = None

    @field_validator("report_type")
    @classmethod
    def validate_report_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in REPORT_TYPES:
            raise ValueError("invalid report_type")
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

    @field_validator("chart_image_mode")
    @classmethod
    def validate_chart_image_mode(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in CHART_IMAGE_MODES:
            raise ValueError("invalid chart_image_mode")
        return cleaned


class WordReportRead(BaseModel):
    artifact_id: str
    form_id: str
    project_id: str
    report_type: str
    file_name: str
    file_path: str
    mime_type: str
    file_size_bytes: int
    sections: list[WordReportSectionRead]
    table_count: int
    chart_image_count: int
    chart_placeholder_count: int
    chart_image_artifact_ids: list[str]
    analysis_run_count: int
    warnings: list[str]
    created_at: datetime


class AvailableWordAnalysisRunRead(BaseModel):
    id: str
    analysis_type: str
    created_at: datetime


class WordReportOptionsRead(BaseModel):
    form_id: str
    available_report_types: list[str]
    available_analysis_runs: list[AvailableWordAnalysisRunRead]
    available_orchestrated_runs: list[AvailableWordAnalysisRunRead]
    recommended_report: str
    available_sections: list[str]
