from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


SCORING_LEVELS = {"instrument", "dimension", "project_variable", "custom"}
AGGREGATION_METHODS = {"sum", "mean", "weighted_mean"}
MISSING_POLICIES = {"strict_complete", "allow_partial", "prorate_if_threshold_met"}
CONTROL_TYPES = {"lie", "attention", "infrequency", "consistency", "custom"}
RULE_TYPES = {"sum_threshold", "mean_threshold", "any_failed", "count_failed", "paired_inconsistency", "custom"}
COMPARISON_OPERATORS = {"gt", "gte", "lt", "lte", "eq"}


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class ScoreBandBase(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=100)
    min_value: float
    max_value: float
    interpretation: str | None = None
    recommendation: str | None = None
    severity_order: int = 0
    color_hint: str | None = Field(default=None, max_length=50)

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("label must not be empty")
        return cleaned

    @field_validator("code", "interpretation", "recommendation", "color_hint")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("max_value")
    @classmethod
    def validate_range(cls, value: float, info) -> float:
        min_value = info.data.get("min_value")
        if min_value is not None and value < min_value:
            raise ValueError("max_value must be greater than or equal to min_value")
        return value


class ScoreBandCreate(ScoreBandBase):
    pass


class ScoreBandUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=100)
    min_value: float | None = None
    max_value: float | None = None
    interpretation: str | None = None
    recommendation: str | None = None
    severity_order: int | None = None
    color_hint: str | None = Field(default=None, max_length=50)

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("code", "interpretation", "recommendation", "color_hint")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)


class ScoreBandRead(ScoreBandBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scoring_config_id: str
    created_at: datetime
    updated_at: datetime


class ScoringConfigBase(BaseModel):
    instrument_id: str | None = None
    dimension_id: str | None = None
    project_variable_id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=100)
    scoring_level: str
    aggregation_method: str = "mean"
    missing_policy: str = "allow_partial"
    min_answered_items: int | None = Field(default=None, ge=0)
    min_completion_percent: float | None = Field(default=None, ge=0, le=100)
    reverse_scoring_enabled: bool = True
    score_min: float | None = None
    score_max: float | None = None
    interpretation_enabled: bool = True
    config_json: dict[str, Any] | list[Any] | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("scoring_level")
    @classmethod
    def validate_scoring_level(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in SCORING_LEVELS:
            raise ValueError("invalid scoring_level")
        return cleaned

    @field_validator("aggregation_method")
    @classmethod
    def validate_aggregation_method(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in AGGREGATION_METHODS:
            raise ValueError("invalid aggregation_method")
        return cleaned

    @field_validator("missing_policy")
    @classmethod
    def validate_missing_policy(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in MISSING_POLICIES:
            raise ValueError("invalid missing_policy")
        return cleaned


class ScoringConfigCreate(ScoringConfigBase):
    bands: list[ScoreBandCreate] = Field(default_factory=list)


class ScoringConfigUpdate(BaseModel):
    instrument_id: str | None = None
    dimension_id: str | None = None
    project_variable_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=100)
    scoring_level: str | None = None
    aggregation_method: str | None = None
    missing_policy: str | None = None
    min_answered_items: int | None = Field(default=None, ge=0)
    min_completion_percent: float | None = Field(default=None, ge=0, le=100)
    reverse_scoring_enabled: bool | None = None
    score_min: float | None = None
    score_max: float | None = None
    interpretation_enabled: bool | None = None
    config_json: dict[str, Any] | list[Any] | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("scoring_level")
    @classmethod
    def validate_scoring_level(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in SCORING_LEVELS:
            raise ValueError("invalid scoring_level")
        return cleaned

    @field_validator("aggregation_method")
    @classmethod
    def validate_aggregation_method(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in AGGREGATION_METHODS:
            raise ValueError("invalid aggregation_method")
        return cleaned

    @field_validator("missing_policy")
    @classmethod
    def validate_missing_policy(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in MISSING_POLICIES:
            raise ValueError("invalid missing_policy")
        return cleaned


class ScoringConfigRead(ScoringConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    form_id: str
    bands: list[ScoreBandRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ScoringConfigListRead(BaseModel):
    form_id: str
    total: int
    items: list[ScoringConfigRead]
    warnings: list[str] = Field(default_factory=list)


class ControlScaleBase(BaseModel):
    instrument_id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=100)
    control_type: str
    rule_type: str
    threshold: float | None = None
    comparison_operator: str | None = None
    flag_level: str = "warning"
    message: str | None = None
    config_json: dict[str, Any] | list[Any] | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned

    @field_validator("code", "message")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("control_type")
    @classmethod
    def validate_control_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in CONTROL_TYPES:
            raise ValueError("invalid control_type")
        return cleaned

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in RULE_TYPES:
            raise ValueError("invalid rule_type")
        return cleaned

    @field_validator("comparison_operator")
    @classmethod
    def validate_comparison_operator(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in COMPARISON_OPERATORS:
            raise ValueError("invalid comparison_operator")
        return cleaned

    @field_validator("flag_level")
    @classmethod
    def validate_flag_level(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"warning", "invalid"}:
            raise ValueError("invalid flag_level")
        return cleaned


class ControlScaleItemCreate(BaseModel):
    question_id: str
    expected_option_id: str | None = None
    expected_value_text: str | None = None
    expected_value_number: float | None = None
    fail_if_selected: bool = False
    weight: float = 1.0
    pair_group: str | None = None

    @field_validator("question_id", "expected_option_id", "expected_value_text", "pair_group")
    @classmethod
    def normalize_ids(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)


class ControlScaleItemRead(ControlScaleItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    control_scale_id: str
    created_at: datetime
    updated_at: datetime


class ControlScaleCreate(ControlScaleBase):
    items: list[ControlScaleItemCreate] = Field(default_factory=list)


class ControlScaleUpdate(BaseModel):
    instrument_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=100)
    control_type: str | None = None
    rule_type: str | None = None
    threshold: float | None = None
    comparison_operator: str | None = None
    flag_level: str | None = None
    message: str | None = None
    config_json: dict[str, Any] | list[Any] | None = None
    is_active: bool | None = None

    @field_validator("name", "code", "message")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("control_type")
    @classmethod
    def validate_control_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in CONTROL_TYPES:
            raise ValueError("invalid control_type")
        return cleaned

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in RULE_TYPES:
            raise ValueError("invalid rule_type")
        return cleaned

    @field_validator("comparison_operator")
    @classmethod
    def validate_comparison_operator(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in COMPARISON_OPERATORS:
            raise ValueError("invalid comparison_operator")
        return cleaned

    @field_validator("flag_level")
    @classmethod
    def validate_flag_level(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in {"warning", "invalid"}:
            raise ValueError("invalid flag_level")
        return cleaned


class ControlScaleRead(ControlScaleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    form_id: str
    items: list[ControlScaleItemRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ResponseScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    form_id: str
    response_id: str
    scoring_config_id: str
    instrument_id: str | None
    dimension_id: str | None
    project_variable_id: str | None
    raw_score: float | None
    mean_score: float | None
    weighted_score: float | None
    final_score: float | None
    answered_items: int
    missing_items: int
    total_items: int
    completion_percent: float | None
    band_id: str | None
    band_label: str | None
    interpretation: str | None
    validity_status: str
    warnings_json: dict[str, Any] | list[Any] | None
    created_at: datetime
    updated_at: datetime


class ResponseControlFlagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    form_id: str
    response_id: str
    control_scale_id: str
    score: float | None
    failed_items: int
    total_items: int
    flag_status: str
    message: str | None
    details_json: dict[str, Any] | list[Any] | None
    created_at: datetime
    updated_at: datetime


class ScoringRunRequest(BaseModel):
    include_discarded: bool = False
    recalculate: bool = True
    store_result: bool = True


class ScoringRunRead(BaseModel):
    analysis_run_id: str | None
    form_id: str
    project_id: str
    total_responses: int
    scored_responses: int
    valid_responses: int
    warning_responses: int
    invalid_responses: int
    warnings: list[str]
    score_results: list[ResponseScoreRead]
    control_flags: list[ResponseControlFlagRead]


class ScoringPreviewRead(BaseModel):
    form_id: str
    warnings: list[str]
    score_results: list[ResponseScoreRead]
    control_flags: list[ResponseControlFlagRead]


class ScoringBandDistributionRead(BaseModel):
    scoring_config_id: str
    scoring_config_name: str
    level: str
    n: int
    percent: float
    interpretation: str | None = None


class ControlScaleSummaryRead(BaseModel):
    control_scale_id: str
    name: str
    flag_status: str
    n: int
    percent: float


class ScoringResultsRead(BaseModel):
    form_id: str
    total_responses: int
    scored_responses: int
    valid_responses: int
    warning_responses: int
    invalid_responses: int
    band_distribution: list[ScoringBandDistributionRead]
    control_flags: list[ControlScaleSummaryRead]
    warnings: list[str]


class ScoredDatasetRead(BaseModel):
    form_id: str
    total_rows: int
    columns: list[str]
    rows: list[dict[str, Any]]
    warnings: list[str]


class ScoringOptionsRead(BaseModel):
    form_id: str
    instruments: list[dict[str, Any]]
    dimensions: list[dict[str, Any]]
    scored_questions: list[dict[str, Any]]
    reverse_scored_questions: list[dict[str, Any]]
    configs: list[ScoringConfigRead]
    control_scales: list[ControlScaleRead]
