from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AnalysisTargetInput(BaseModel):
    target_type: str
    target_id: str
    role: str | None = None
    label: str | None = None

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"question", "dimension", "instrument", "project_variable"}:
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
        allowed = {"x", "y", "outcome", "group", "row", "column", "target"}
        if cleaned not in allowed:
            raise ValueError("invalid role")
        return cleaned


class AnalysisTargetRead(BaseModel):
    target_type: str
    target_id: str
    role: str | None = None
    label: str


class AnalysisRequestOptions(BaseModel):
    max_targets: int = Field(default=10, ge=2, le=50)
    max_pairwise_tests: int = Field(default=30, ge=1, le=500)
    include_normality: bool = True
    include_descriptives: bool = True
    include_recommendations: bool = True
    prefer_non_parametric: bool = False
    force_method: str | None = None

    @field_validator("force_method")
    @classmethod
    def normalize_force_method(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        return cleaned or None


class OrchestratedAnalysisRequest(BaseModel):
    analysis_goal: str
    targets: list[AnalysisTargetInput] = Field(default_factory=list)
    method: str = Field(default="auto")
    alpha: float = Field(default=0.05, ge=0.001, le=0.20)
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = Field(default="mean")
    store_result: bool = True
    options: AnalysisRequestOptions | None = None

    @field_validator("analysis_goal")
    @classmethod
    def validate_analysis_goal(cls, value: str) -> str:
        cleaned = value.strip().lower()
        allowed = {
            "descriptive_summary",
            "correlation",
            "correlation_matrix",
            "group_comparison",
            "categorical_association",
            "full_form_scan",
        }
        if cleaned not in allowed:
            raise ValueError("invalid analysis_goal")
        return cleaned

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        cleaned = value.strip().lower()
        return cleaned or "auto"

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"sum", "mean"}:
            raise ValueError("score_aggregation must be sum or mean")
        return cleaned


class FullScanRequest(BaseModel):
    alpha: float = Field(default=0.05, ge=0.001, le=0.20)
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = Field(default="mean")
    store_result: bool = True
    options: AnalysisRequestOptions | None = None

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"sum", "mean"}:
            raise ValueError("score_aggregation must be sum or mean")
        return cleaned


class AnalysisAssumptionRead(BaseModel):
    name: str
    status: str
    description: str
    evidence: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        cleaned = value.strip().lower()
        allowed = {"passed", "failed", "warning", "not_checked", "not_applicable"}
        if cleaned not in allowed:
            raise ValueError("invalid assumption status")
        return cleaned


class AnalysisResultBlockRead(BaseModel):
    block_type: str
    title: str
    summary: str
    payload: dict[str, Any] | list[Any] | None

    @field_validator("block_type")
    @classmethod
    def validate_block_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        allowed = {
            "descriptive",
            "normality",
            "decision",
            "correlation",
            "group_comparison",
            "categorical_association",
            "scoring",
            "quality",
            "recommendation",
        }
        if cleaned not in allowed:
            raise ValueError("invalid block_type")
        return cleaned


class ApaTableBlockRead(BaseModel):
    table_type: str
    suggested_title: str
    source_result: str
    columns: list[str]
    rows: list[dict[str, Any]]
    notes: list[str]
    ready_for_apa: bool

    @field_validator("table_type")
    @classmethod
    def validate_table_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        allowed = {
            "frequencies",
            "descriptives",
            "normality",
            "correlation",
            "group_comparison",
            "categorical_association",
            "scoring_summary",
            "score_band_distribution",
            "control_scale_flags",
        }
        if cleaned not in allowed:
            raise ValueError("invalid table_type")
        return cleaned


class ChartBlockRead(BaseModel):
    chart_type: str
    suggested_title: str
    x_target: str | None = None
    y_target: str | None = None
    group_target: str | None = None
    data_source: str
    recommended: bool
    editable_options: dict[str, Any]

    @field_validator("chart_type")
    @classmethod
    def validate_chart_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        allowed = {"bar", "grouped_bar", "pie", "donut", "histogram", "boxplot", "scatter", "heatmap", "mosaic"}
        if cleaned not in allowed:
            raise ValueError("invalid chart_type")
        return cleaned


class ExportBlockRead(BaseModel):
    export_type: str
    label: str
    available_now: bool
    endpoint: str | None = None
    notes: list[str]

    @field_validator("export_type")
    @classmethod
    def validate_export_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        allowed = {"excel", "word_future", "apa_table_future", "chart_future"}
        if cleaned not in allowed:
            raise ValueError("invalid export_type")
        return cleaned


class OrchestratedAnalysisRead(BaseModel):
    form_id: str
    project_id: str
    analysis_goal: str
    status: str
    analysis_run_id: str | None
    title: str
    executive_summary: str
    what_was_analyzed: str
    main_result: str
    statistical_result: str
    academic_interpretation: str
    plain_language_explanation: str
    assumptions: list[AnalysisAssumptionRead]
    warnings: list[str]
    recommended_next_steps: list[str]
    result_blocks: list[AnalysisResultBlockRead]
    apa_table_blocks: list[ApaTableBlockRead]
    chart_blocks: list[ChartBlockRead]
    export_blocks: list[ExportBlockRead]
    raw_results_summary: dict[str, Any]

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        cleaned = value.strip().lower()
        allowed = {"completed", "completed_with_warnings", "not_applicable", "failed"}
        if cleaned not in allowed:
            raise ValueError("invalid status")
        return cleaned


class AnalysisWorkflowRead(BaseModel):
    analysis_goal: str
    title: str
    description: str
    required_roles: list[str]


class AnalysisOptionsRead(BaseModel):
    form_id: str
    goals: list[str]
    available_targets: dict[str, list[AnalysisTargetRead]]
    recommended_workflows: list[AnalysisWorkflowRead]


class RecentAnalysisRunRead(BaseModel):
    id: str
    analysis_type: str
    status: str
    created_at: datetime
    result_preview: dict[str, Any] | None = None


class AnalysisSummaryRead(BaseModel):
    form_id: str
    project_id: str
    total_responses: int
    included_responses: int
    data_quality: dict[str, Any]
    available_analyses: list[str]
    recent_analysis_runs: list[RecentAnalysisRunRead]
    warnings: list[str]
