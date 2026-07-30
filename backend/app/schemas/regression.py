from pydantic import BaseModel, Field, field_validator

from app.schemas.correlation import CorrelationTargetInput, CorrelationTargetRead


class RegressionRequest(BaseModel):
    dependent: CorrelationTargetInput
    independents: list[CorrelationTargetInput]
    alpha: float = Field(default=0.05, ge=0.001, le=0.20)
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    score_aggregation: str = Field(default="sum")
    store_result: bool = True

    @field_validator("independents")
    @classmethod
    def validate_independents(cls, value: list[CorrelationTargetInput]) -> list[CorrelationTargetInput]:
        if not value:
            raise ValueError("independents must contain at least one item")
        return value

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"sum", "mean"}:
            raise ValueError("score_aggregation must be sum or mean")
        return cleaned


class RegressionCoefficientRead(BaseModel):
    target_type: str
    target_id: str
    label: str
    coefficient: float | None
    standard_error: float | None
    t_value: float | None
    p_value: float | None
    significant: bool
    ci_lower: float | None
    ci_upper: float | None


class RegressionResultRead(BaseModel):
    form_id: str
    project_id: str
    dependent_target: CorrelationTargetRead
    independent_targets: list[CorrelationTargetRead]
    alpha: float
    valid_n: int
    intercept: float | None
    r_squared: float | None
    adjusted_r_squared: float | None
    f_statistic: float | None
    f_p_value: float | None
    classification: str
    interpretation: str
    null_hypothesis: str
    alternative_hypothesis: str
    coefficients: list[RegressionCoefficientRead]
    warnings: list[str]


class RegressionRunRead(BaseModel):
    analysis_run_id: str | None
    result: RegressionResultRead
