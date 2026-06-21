from pydantic import BaseModel, Field, field_validator

from app.schemas.normality import NormalityTestResultRead


class ComparisonTargetInput(BaseModel):
    target_type: str
    target_id: str
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


class ComparisonTargetRead(BaseModel):
    target_type: str
    target_id: str
    label: str


class GroupComparisonRequest(BaseModel):
    outcome: ComparisonTargetInput
    group: ComparisonTargetInput
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
        allowed = {
            "auto",
            "t_student_independent",
            "welch_t",
            "mann_whitney_u",
            "anova_one_way",
            "kruskal_wallis",
        }
        if cleaned not in allowed:
            raise ValueError("invalid method")
        return cleaned

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"sum", "mean"}:
            raise ValueError("score_aggregation must be sum or mean")
        return cleaned


class GroupDescriptiveRead(BaseModel):
    group_label: str
    group_value: str
    n: int
    missing_n: int
    mean: float | None
    median: float | None
    standard_deviation: float | None
    variance: float | None
    minimum: float | None
    maximum: float | None
    range: float | None
    percentile_25: float | None
    percentile_75: float | None


class VarianceHomogeneityRead(BaseModel):
    method: str
    statistic: float | None
    p_value: float | None
    alpha: float
    classification: str
    interpretation: str
    warnings: list[str]


class EffectSizeRead(BaseModel):
    name: str
    value: float | None
    magnitude: str
    interpretation: str
    warnings: list[str]


class GroupComparisonResultRead(BaseModel):
    form_id: str
    project_id: str
    method_requested: str
    method_used: str
    alpha: float
    outcome_target: ComparisonTargetRead
    group_target: ComparisonTargetRead
    total_n: int
    valid_n: int
    missing_n: int
    group_count: int
    groups: list[GroupDescriptiveRead]
    statistic: float | None
    p_value: float | None
    degrees_of_freedom: str | None
    classification: str
    effect_size: EffectSizeRead | None
    variance_homogeneity: VarianceHomogeneityRead | None
    normality_by_group: list[NormalityTestResultRead]
    interpretation: str
    warnings: list[str]
    required_next_steps: list[str]
    assumptions: list[str]


class GroupComparisonRunRead(BaseModel):
    analysis_run_id: str | None
    result: GroupComparisonResultRead


class GroupComparisonOptionsRead(BaseModel):
    outcomes: list[ComparisonTargetRead]
    groups: list[ComparisonTargetRead]
