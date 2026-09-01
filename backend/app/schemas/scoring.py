from __future__ import annotations

from pydantic import BaseModel, Field


class ScoreRunSummary(BaseModel):
    analysis_run_id: int
    study_id: int
    sessions_processed: int
    scores_created: int
    constructs_scored: int
    algorithm_version: str


class ResultBandCount(BaseModel):
    band_id: int | None
    code: str
    label: str
    classification_code: str | None = None
    color_hint: str | None
    n: int | None
    pct: float | None
    suppressed: bool = False


class ConstructBaremResult(BaseModel):
    construct_id: int
    parent_id: int | None = None
    construct_code: str
    construct_name: str
    construct_type: str
    n_valid: int
    suppressed: bool
    mean_score: float | None
    median_score: float | None
    priority_rank: int | None = None
    bands: list[ResultBandCount] = Field(default_factory=list)


class StudyResultsOverview(BaseModel):
    study_id: int
    study_name: str
    study_type: str
    instrument_id: int | None = None
    instrument_name: str | None = None
    instrument_version_code: str | None = None
    analysis_run_id: int | None
    algorithm_version: str | None
    instrument_version_id: int | None
    barem_id: int | None
    barem_name: str | None
    barem_status: str | None = None
    official_equivalence: bool = False
    n_completed: int
    min_publishable_n: int
    results: list[ConstructBaremResult] = Field(default_factory=list)
