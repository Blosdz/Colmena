from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import metadata_field
from app.schemas.questions import OptionSetOptionInput, QuestionRead

VariableType = Literal["QUESTION", "DERIVED", "DEMOGRAPHIC", "EXOGENOUS", "CONSTRUCT_SCORE", "SYSTEM"]
DataType = Literal["INTEGER", "DECIMAL", "TEXT", "BOOLEAN", "DATE", "DATETIME", "CATEGORY"]
MeasurementLevel = Literal["NOMINAL", "ORDINAL", "SCALE", "BINARY", "TEXT"]
VariableRole = Literal[
    "INDEPENDENT", "DEPENDENT", "CONTROL", "EXOGENOUS", "DESCRIPTIVE", "OUTCOME", "NONE"
]


class VariableCreate(BaseModel):
    study_id: int | None = None
    instrument_version_id: int | None = None
    question_id: int | None = None
    construct_id: int | None = None
    code: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=255)
    label: str | None = None
    variable_type: VariableType
    data_type: DataType
    measurement_level: MeasurementLevel
    role: VariableRole = "NONE"
    is_editable: bool = True
    formula: str | None = None
    metadata: dict = Field(default_factory=dict)


class VariableUpdate(BaseModel):
    """Campos editables de una variable (harness §8).

    `data_type` se permite aquí, pero el servicio valida antes de aplicar un
    cambio destructivo (p.ej. TEXT -> INTEGER) — ver VariableService.
    """

    name: str | None = None
    label: str | None = None
    measurement_level: MeasurementLevel | None = None
    role: VariableRole | None = None
    data_type: DataType | None = None
    is_editable: bool | None = None
    formula: str | None = None
    metadata: dict | None = None


class VariableRead(BaseModel):
    id: int
    public_id: uuid.UUID
    project_id: int
    study_id: int | None
    instrument_version_id: int | None
    question_id: int | None
    construct_id: int | None
    code: str
    name: str
    label: str | None
    variable_type: str
    data_type: str
    measurement_level: str
    role: str
    is_editable: bool
    formula: str | None
    metadata: dict = metadata_field()
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VariableBatchItem(BaseModel):
    id: int
    patch: VariableUpdate


class VariableBatchUpdate(BaseModel):
    items: list[VariableBatchItem]


class ExogenousFieldCreate(BaseModel):
    instrument_version_id: int
    code: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=255)
    question_text: str = Field(min_length=1)
    data_type: DataType
    measurement_level: MeasurementLevel
    is_required: bool = False
    sort_order: int | None = None
    options: list[OptionSetOptionInput] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ExogenousFieldRead(BaseModel):
    variable: VariableRead
    question: QuestionRead
