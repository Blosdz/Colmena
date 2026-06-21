from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.normality import NormalityTestResultRead


class CorrelationTargetInput(BaseModel):
    target_type: str
    target_id: str
    label: str | None = None

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"question", "dimension", "instrument", "project_variable"}:
            raise ValueError("target_type must be question, dimension, instrument, or project_variable")
        return cleaned

    @field_validator("target_id")
    @classmethod
    def validate_target_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("target_id must not be empty")
        return cleaned


class CorrelationTargetRead(BaseModel):
    target_type: str
    target_id: str
    label: str


class CorrelationRequest(BaseModel):
    x: CorrelationTargetInput
    y: CorrelationTargetInput
    method: str = Field(default="auto")
    alpha: float = Field(default=0.05, ge=0.001, le=0.20)
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = Field(default="mean")
    store_result: bool = True

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"auto", "pearson", "spearman", "kendall", "point_biserial"}:
            raise ValueError("method must be auto, pearson, spearman, kendall, or point_biserial")
        return cleaned

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"sum", "mean"}:
            raise ValueError("score_aggregation must be sum or mean")
        return cleaned


class CorrelationResultRead(BaseModel):
    form_id: str
    project_id: str
    method_requested: str
    method_used: str
    alpha: float
    x_target: CorrelationTargetRead
    y_target: CorrelationTargetRead
    valid_n: int
    missing_n: int
    coefficient: float | None
    p_value: float | None
    direction: str
    magnitude: str
    significance: str
    classification: str
    interpretation: str
    null_hypothesis: str
    alternative_hypothesis: str
    method_justification: str
    warnings: list[str]
    normality_context: dict[str, NormalityTestResultRead | None]
    assumptions: list[str]


class CorrelationRunRead(BaseModel):
    analysis_run_id: str | None
    result: CorrelationResultRead


class CorrelationMatrixRequest(BaseModel):
    targets: list[CorrelationTargetInput]
    method: str = Field(default="auto")
    alpha: float = Field(default=0.05, ge=0.001, le=0.20)
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = Field(default="mean")
    store_result: bool = True

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, value: list[CorrelationTargetInput]) -> list[CorrelationTargetInput]:
        if len(value) < 2:
            raise ValueError("targets must contain at least two items")
        return value

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"auto", "pearson", "spearman", "kendall", "point_biserial"}:
            raise ValueError("method must be auto, pearson, spearman, kendall, or point_biserial")
        return cleaned

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"sum", "mean"}:
            raise ValueError("score_aggregation must be sum or mean")
        return cleaned


class CorrelationMatrixCellRead(BaseModel):
    row_target_id: str
    column_target_id: str
    row_label: str
    column_label: str
    method_used: str
    valid_n: int
    coefficient: float | None
    p_value: float | None
    magnitude: str
    significance: str
    warnings: list[str]


class CorrelationMatrixRead(BaseModel):
    form_id: str
    project_id: str
    method_requested: str
    alpha: float
    targets: list[CorrelationTargetRead]
    cells: list[CorrelationMatrixCellRead]
    warnings: list[str]
    analysis_run_id: str | None
