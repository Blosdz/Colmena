from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


CHART_TYPES = {
    "bar",
    "horizontal_bar",
    "grouped_bar",
    "stacked_bar",
    "pie",
    "donut",
    "histogram",
    "boxplot",
    "scatter",
    "heatmap",
    "line",
    "mosaic_future",
}
SOURCE_TYPES = {"live", "analysis_run", "orchestrated", "chart_block"}
THEMES = {"academic_light", "colmena_premium", "presentation_clean", "monochrome_apa"}


class ChartTargetInput(BaseModel):
    target_type: str
    target_id: str
    role: str | None = None
    label: str | None = None

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        allowed = {"question", "dimension", "instrument", "project_variable", "analysis_run"}
        if cleaned not in allowed:
            raise ValueError("invalid target_type")
        return cleaned

    @field_validator("target_id")
    @classmethod
    def validate_target_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("target_id must not be empty")
        return cleaned

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        allowed = {"x", "y", "outcome", "group", "row", "column", "value", "target"}
        if cleaned not in allowed:
            raise ValueError("invalid role")
        return cleaned


class ChartEditableOptionsRead(BaseModel):
    can_change_chart_type: bool
    available_chart_types: list[str]
    can_edit_title: bool
    can_edit_subtitle: bool
    can_edit_axis_labels: bool
    can_show_percentages: bool
    can_show_frequencies: bool
    can_show_values: bool
    can_show_legend: bool
    can_change_palette: bool
    can_change_orientation: bool
    can_group_by: bool
    can_export_future: bool
    notes: list[str]


class ChartSpecRead(BaseModel):
    chart_id: str
    form_id: str
    project_id: str
    chart_type: str
    title: str
    subtitle: str | None = None
    description: str
    source_type: str
    source_reference: str | None = None
    targets: list[ChartTargetInput]
    data: dict[str, Any] | list[Any]
    encoding: dict[str, Any]
    plotly_data: list[dict[str, Any]]
    plotly_layout: dict[str, Any]
    plotly_config: dict[str, Any]
    theme: dict[str, Any]
    editable_options: ChartEditableOptionsRead
    recommended_alternatives: list[str]
    academic_note: str
    plain_language_explanation: str
    warnings: list[str]
    ready_for_frontend: bool
    ready_for_export: bool
    created_at: datetime

    @field_validator("chart_type")
    @classmethod
    def validate_chart_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in CHART_TYPES:
            raise ValueError("invalid chart_type")
        return cleaned

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in SOURCE_TYPES:
            raise ValueError("invalid source_type")
        return cleaned


class ChartGenerateRequest(BaseModel):
    chart_type: str | None = None
    source_type: str
    analysis_goal: str | None = None
    analysis_run_id: str | None = None
    targets: list[ChartTargetInput] | None = None
    theme: str = "colmena_premium"
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = "mean"
    options: dict[str, Any] | None = None

    @field_validator("chart_type")
    @classmethod
    def validate_chart_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in CHART_TYPES:
            raise ValueError("invalid chart_type")
        return cleaned

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"live", "analysis_run", "orchestrated"}:
            raise ValueError("invalid source_type")
        return cleaned

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in THEMES:
            raise ValueError("invalid theme")
        return cleaned

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"mean", "sum"}:
            raise ValueError("score_aggregation must be mean or sum")
        return cleaned


class ChartBatchRequest(BaseModel):
    source_type: str
    analysis_run_ids: list[str] | None = None
    chart_types: list[str] | None = None
    theme: str = "colmena_premium"
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = "mean"
    options: dict[str, Any] | None = None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"live", "analysis_run", "orchestrated"}:
            raise ValueError("invalid source_type")
        return cleaned

    @field_validator("chart_types")
    @classmethod
    def validate_chart_types(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned_values: list[str] = []
        for item in value:
            cleaned = item.strip().lower()
            if cleaned not in CHART_TYPES:
                raise ValueError("invalid chart_type in batch")
            cleaned_values.append(cleaned)
        return cleaned_values

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in THEMES:
            raise ValueError("invalid theme")
        return cleaned

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"mean", "sum"}:
            raise ValueError("score_aggregation must be mean or sum")
        return cleaned


class ChartBatchRead(BaseModel):
    form_id: str
    project_id: str
    total_charts: int
    charts: list[ChartSpecRead]
    warnings: list[str]


class ChartRecommendationRead(BaseModel):
    chart_type: str
    analysis_goal: str
    reason: str


class CompatibleChartAnalysisRunRead(BaseModel):
    id: str
    analysis_type: str
    created_at: datetime


class ChartOptionsRead(BaseModel):
    form_id: str
    available_chart_types: list[str]
    available_themes: list[str]
    recommended_charts: list[ChartRecommendationRead]
    available_targets: dict[str, list[ChartTargetInput]]
    analysis_runs: list[CompatibleChartAnalysisRunRead]


class ChartExportRequest(BaseModel):
    format: str
    source_type: str
    chart_types: list[str] | None = None
    analysis_run_ids: list[str] | None = None
    theme: str = "colmena_premium"
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = "mean"
    options: dict[str, Any] | None = None

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned != "json":
            raise ValueError("invalid export format")
        return cleaned

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"live", "analysis_run", "orchestrated"}:
            raise ValueError("invalid source_type")
        return cleaned

    @field_validator("chart_types")
    @classmethod
    def validate_chart_types(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned_values: list[str] = []
        for item in value:
            cleaned = item.strip().lower()
            if cleaned not in CHART_TYPES:
                raise ValueError("invalid chart_type")
            cleaned_values.append(cleaned)
        return cleaned_values

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in THEMES:
            raise ValueError("invalid theme")
        return cleaned


class ChartExportRead(BaseModel):
    artifact_id: str | None
    file_name: str
    file_path: str
    mime_type: str
    chart_count: int
    created_at: datetime
