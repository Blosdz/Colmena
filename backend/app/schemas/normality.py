from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class NormalityDescriptiveContextRead(BaseModel):
    mean: float | None
    median: float | None
    standard_deviation: float | None
    skewness: float | None
    kurtosis: float | None
    minimum: float | None
    maximum: float | None


class NormalityTestResultRead(BaseModel):
    target_type: str
    target_id: str
    target_name: str
    method: str
    statistic: float | None
    p_value: float | None
    alpha: float
    valid_n: int
    missing_n: int
    missing_percent: float
    classification: str
    interpretation: str
    warnings: list[str]
    descriptive_context: NormalityDescriptiveContextRead


class NormalityReportRead(BaseModel):
    form_id: str
    project_id: str
    method: str
    alpha: float
    include_discarded: bool
    score_aggregation: str
    total_targets: int
    applicable_targets: int
    normal_count: int
    non_normal_count: int
    inconclusive_count: int
    not_applicable_count: int
    results: list[NormalityTestResultRead]
    warnings: list[str]


class NormalityRunRequest(BaseModel):
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
        if cleaned not in {"auto", "shapiro", "lilliefors", "dagostino"}:
            raise ValueError("method must be auto, shapiro, lilliefors, or dagostino")
        return cleaned

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"sum", "mean"}:
            raise ValueError("score_aggregation must be sum or mean")
        return cleaned


class NormalityRunRead(BaseModel):
    analysis_run_id: str | None
    report: NormalityReportRead
    created_at: datetime | None = None
