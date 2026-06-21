from pydantic import BaseModel, Field, field_validator


class CategoricalAssociationTargetInput(BaseModel):
    target_type: str
    target_id: str
    label: str | None = None

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"question", "project_variable"}:
            raise ValueError("invalid target_type")
        return cleaned

    @field_validator("target_id")
    @classmethod
    def validate_target_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("target_id must not be empty")
        return cleaned


class CategoricalAssociationTargetRead(BaseModel):
    target_type: str
    target_id: str
    label: str


class CategoricalAssociationRequest(BaseModel):
    row: CategoricalAssociationTargetInput
    column: CategoricalAssociationTargetInput
    method: str = Field(default="auto")
    alpha: float = Field(default=0.05, ge=0.001, le=0.20)
    decimals: int = Field(default=3, ge=0, le=6)
    include_discarded: bool = False
    store_result: bool = True

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"auto", "chi_square", "fisher_exact"}:
            raise ValueError("invalid method")
        return cleaned


class ContingencyTableCellRead(BaseModel):
    row_label: str
    row_value: str
    column_label: str
    column_value: str
    observed: int
    expected: float | None
    total_percent: float | None
    row_percent: float | None
    column_percent: float | None


class AssociationEffectSizeRead(BaseModel):
    name: str
    value: float | None
    magnitude: str
    interpretation: str
    warnings: list[str]


class CategoricalAssociationResultRead(BaseModel):
    form_id: str
    project_id: str
    method_requested: str
    method_used: str
    alpha: float
    row_target: CategoricalAssociationTargetRead
    column_target: CategoricalAssociationTargetRead
    total_n: int
    valid_n: int
    missing_n: int
    row_categories: list[str]
    column_categories: list[str]
    observed_table: list[list[int]]
    expected_table: list[list[float]] | None
    cells: list[ContingencyTableCellRead]
    statistic: float | None
    degrees_of_freedom: int | None
    p_value: float | None
    odds_ratio: float | None
    classification: str
    effect_size: AssociationEffectSizeRead | None
    interpretation: str
    warnings: list[str]
    required_next_steps: list[str]
    assumptions: list[str]


class CategoricalAssociationRunRead(BaseModel):
    analysis_run_id: str | None
    result: CategoricalAssociationResultRead


class CategoricalAssociationOptionsRead(BaseModel):
    form_id: str
    categorical_targets: list[CategoricalAssociationTargetRead]
