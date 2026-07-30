from datetime import datetime

from pydantic import BaseModel, Field


class ItemReliabilityRead(BaseModel):
    item_id: str
    label: str | None
    valid_n: int
    mean: float | None
    variance: float | None
    item_total_correlation: float | None
    alpha_if_deleted: float | None


class CronbachAlphaRead(BaseModel):
    alpha: float | None
    standardized_alpha: float | None
    n_items: int
    n_valid_cases: int
    n_excluded_cases: int
    average_inter_item_correlation: float | None
    sum_item_variances: float | None
    total_variance: float | None
    classification: str
    interpretation: str
    items: list[ItemReliabilityRead]
    warnings: list[str]


class ReliabilityTargetRead(BaseModel):
    target_type: str
    target_id: str
    target_name: str
    item_count: int
    result: CronbachAlphaRead


class ItemLoadingRead(BaseModel):
    item_id: str
    label: str | None
    standardized_loading: float | None
    error_variance: float | None


class CompositeReliabilityRead(BaseModel):
    composite_reliability: float | None
    ave: float | None
    n_items: int
    n_valid_cases: int
    convergence: bool
    classification: str
    interpretation: str
    items: list[ItemLoadingRead]
    warnings: list[str]


class CompositeReliabilityTargetRead(BaseModel):
    target_type: str
    target_id: str
    target_name: str
    item_count: int
    result: CompositeReliabilityRead


class ReliabilityReportRead(BaseModel):
    form_id: str
    project_id: str
    include_discarded: bool
    total_targets: int
    applicable_targets: int
    results: list[ReliabilityTargetRead]
    warnings: list[str]


class CompositeReliabilityReportRead(BaseModel):
    form_id: str
    project_id: str
    include_discarded: bool
    total_targets: int
    applicable_targets: int
    results: list[CompositeReliabilityTargetRead]
    warnings: list[str]


class ReliabilityRunRequest(BaseModel):
    include_discarded: bool = False
    decimals: int = Field(default=3, ge=0, le=6)
    store_result: bool = True


class ReliabilityRunRead(BaseModel):
    analysis_run_id: str | None
    created_at: datetime | None
    report: ReliabilityReportRead
