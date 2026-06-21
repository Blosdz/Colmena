from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FrequencyRowRead(BaseModel):
    label: str | None
    value: str | None
    frequency: int
    percent: float | None
    valid_percent: float | None
    cumulative_percent: float | None


class NumericDescriptiveRead(BaseModel):
    valid_n: int
    missing_n: int
    mean: float | None
    median: float | None
    mode: float | None
    standard_deviation: float | None
    variance: float | None
    minimum: float | None
    maximum: float | None
    range: float | None
    skewness: float | None
    kurtosis: float | None
    percentile_25: float | None
    percentile_50: float | None
    percentile_75: float | None


class QuestionDescriptiveRead(BaseModel):
    question_id: str
    code: str | None
    label: str
    question_type: str
    question_role: str
    measurement_level: str
    data_type: str
    is_scored: bool
    valid_n: int
    missing_n: int
    frequencies: list[FrequencyRowRead]
    numeric: NumericDescriptiveRead | None
    warnings: list[str]


class DimensionDescriptiveRead(BaseModel):
    dimension_id: str
    instrument_id: str
    name: str
    item_count: int
    scored_item_count: int
    aggregation: str
    numeric: NumericDescriptiveRead | None
    warnings: list[str]


class InstrumentDescriptiveRead(BaseModel):
    instrument_id: str
    name: str
    acronym: str | None
    item_count: int
    scored_item_count: int
    aggregation: str
    dimensions: list[DimensionDescriptiveRead]
    numeric: NumericDescriptiveRead | None
    warnings: list[str]


class ProjectVariableDescriptiveRead(BaseModel):
    variable_id: str
    name: str
    variable_role: str
    measurement_level: str
    data_type: str
    question_count: int
    scored_question_count: int
    questions: list[QuestionDescriptiveRead]
    numeric: NumericDescriptiveRead | None
    frequencies: list[FrequencyRowRead]
    warnings: list[str]


class DescriptiveOverviewRead(BaseModel):
    form_id: str
    project_id: str
    total_responses: int
    included_responses: int
    discarded_responses: int
    total_questions: int
    scored_questions: int
    categorical_questions: int
    numeric_questions: int
    missing_overview: dict[str, Any]
    warnings: list[str]


class FormDescriptiveReportRead(BaseModel):
    form_id: str
    project_id: str
    mode: str
    decimals: int
    overview: DescriptiveOverviewRead
    questions: list[QuestionDescriptiveRead]
    dimensions: list[DimensionDescriptiveRead]
    instruments: list[InstrumentDescriptiveRead]
    project_variables: list[ProjectVariableDescriptiveRead]


class DimensionDescriptiveListRead(BaseModel):
    form_id: str
    aggregation: str
    items: list[DimensionDescriptiveRead]


class InstrumentDescriptiveListRead(BaseModel):
    form_id: str
    aggregation: str
    items: list[InstrumentDescriptiveRead]


class ProjectVariableDescriptiveListRead(BaseModel):
    form_id: str
    items: list[ProjectVariableDescriptiveRead]


class CrosstabCellRead(BaseModel):
    row_value: str | None
    column_value: str | None
    count: int
    total_percent: float | None
    row_percent: float | None
    column_percent: float | None


class CrosstabRead(BaseModel):
    form_id: str
    row_question_id: str
    column_question_id: str
    row_question_label: str
    column_question_label: str
    total_n: int
    rows: list[str | None]
    columns: list[str | None]
    cells: list[CrosstabCellRead]
    warnings: list[str]


class AnalysisRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    form_id: str
    analysis_type: str
    status: str
    params_json: dict | list | None
    result_json: dict | list | None
    created_at: datetime


class DescriptiveRunRequest(BaseModel):
    include_discarded: bool = False
    decimals: int = Field(default=3, ge=0, le=6)
    score_aggregation: str = Field(default="mean")
    store_result: bool = True

    @field_validator("score_aggregation")
    @classmethod
    def validate_score_aggregation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"sum", "mean"}:
            raise ValueError("score_aggregation must be sum or mean")
        return cleaned


class DescriptiveRunRead(BaseModel):
    form_id: str
    stored: bool
    analysis_run: AnalysisRunRead | None
    report: FormDescriptiveReportRead
