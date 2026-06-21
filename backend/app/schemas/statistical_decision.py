from pydantic import BaseModel, Field, field_validator

from app.schemas.normality import NormalityTestResultRead


class DecisionVariableInput(BaseModel):
    question_id: str | None = None
    dimension_id: str | None = None
    instrument_id: str | None = None
    project_variable_id: str | None = None
    role: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        allowed = {"x", "y", "outcome", "group", "paired_before", "paired_after"}
        if cleaned not in allowed:
            raise ValueError("invalid role")
        return cleaned

    @field_validator("project_variable_id", "question_id", "dimension_id", "instrument_id")
    @classmethod
    def normalize_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class StatisticalDecisionRequest(BaseModel):
    analysis_goal: str
    variables: list[DecisionVariableInput]
    alpha: float = Field(default=0.05, ge=0.001, le=0.20)
    normality_method: str = Field(default="auto")
    score_aggregation: str = Field(default="mean")
    include_discarded: bool = False
    store_result: bool = False

    @field_validator("analysis_goal")
    @classmethod
    def validate_analysis_goal(cls, value: str) -> str:
        cleaned = value.strip().lower()
        allowed = {
            "correlation",
            "comparison_independent_groups",
            "comparison_related_groups",
            "association_categorical",
            "descriptive_only",
        }
        if cleaned not in allowed:
            raise ValueError("invalid analysis_goal")
        return cleaned

    @field_validator("normality_method")
    @classmethod
    def validate_normality_method(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"auto", "shapiro", "lilliefors", "dagostino"}:
            raise ValueError("invalid normality_method")
        return cleaned

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"sum", "mean"}:
            raise ValueError("score_aggregation must be sum or mean")
        return cleaned


class StatisticalDecisionRead(BaseModel):
    form_id: str
    project_id: str
    analysis_goal: str
    recommended_test: str
    alternative_tests: list[str]
    route: str
    confidence: str
    assumptions_checked: list[str]
    assumptions_failed: list[str]
    required_next_steps: list[str]
    explanation: str
    warnings: list[str]
    normality_results: list[NormalityTestResultRead]
    analysis_run_id: str | None = None
