from pydantic import BaseModel

from app.schemas.normality import NormalityTestResultRead
from app.schemas.reliability import CompositeReliabilityTargetRead, ReliabilityTargetRead
from app.schemas.scoring import VariableBaremoRead


class InstrumentMetadataRead(BaseModel):
    instrument_id: str
    name: str
    acronym: str | None
    author: str | None
    year: int | None
    objective: str | None
    application_mode: str | None
    response_scale_name: str | None
    scale_kind: str | None
    scale_points: int | None
    scale_label: str | None
    n_items: int
    n_dimensions: int
    dimension_names: list[str]


class InstrumentSheetDimensionRead(BaseModel):
    dimension_id: str
    dimension_name: str
    alpha: ReliabilityTargetRead
    composite: CompositeReliabilityTargetRead
    normality_shapiro: NormalityTestResultRead | None
    normality_ks: NormalityTestResultRead | None


class InstrumentSheetRead(BaseModel):
    form_id: str
    project_id: str
    metadata: InstrumentMetadataRead
    alpha: ReliabilityTargetRead
    composite: CompositeReliabilityTargetRead
    normality_shapiro: NormalityTestResultRead | None
    normality_ks: NormalityTestResultRead | None
    dimensions: list[InstrumentSheetDimensionRead]
    baremos: list[VariableBaremoRead]
    warnings: list[str]
