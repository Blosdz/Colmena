from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import metadata_field

ConstructType = Literal["VARIABLE", "DIMENSION", "SUBDIMENSION", "SCALE", "FACTOR", "INDEX"]


class StructureVariableCreate(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=255)
    role: Literal["INDEPENDENT", "DEPENDENT", "CONTROL", "OUTCOME"] = "INDEPENDENT"
    sort_order: int | None = None


class StructureVariableRead(BaseModel):
    id: int
    code: str
    name: str
    role: str
    sort_order: int | None


class ConstructCreate(BaseModel):
    parent_id: int | None = None
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=255)
    construct_type: ConstructType
    description: str | None = None
    sort_order: int | None = None
    metadata: dict = Field(default_factory=dict)


class ConstructUpdate(BaseModel):
    parent_id: int | None = None
    code: str | None = None
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    metadata: dict | None = None


class ConstructRead(BaseModel):
    id: int
    public_id: uuid.UUID
    instrument_version_id: int
    parent_id: int | None
    code: str
    name: str
    construct_type: str
    description: str | None
    sort_order: int | None
    metadata: dict = metadata_field()
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConstructBatchItem(BaseModel):
    id: int
    patch: ConstructUpdate


class ConstructBatchUpdate(BaseModel):
    items: list[ConstructBatchItem]


# --- Asignación ítem <-> constructo (harness §10) ------------------------------

ItemRole = Literal["SCORED", "CONTEXT", "EXCLUDED"]
ScoringDirection = Literal["DIRECT", "REVERSE"]


class ConstructItemCreate(BaseModel):
    question_id: int
    weight: float = 1
    item_role: ItemRole = "SCORED"
    scoring_direction: ScoringDirection | None = None
    sort_order: int | None = None


class ConstructItemUpdate(BaseModel):
    weight: float | None = None
    item_role: ItemRole | None = None
    scoring_direction: ScoringDirection | None = None
    sort_order: int | None = None


class ConstructItemRead(BaseModel):
    construct_id: int
    question_id: int
    weight: float
    item_role: str | None
    scoring_direction: str | None
    sort_order: int | None

    model_config = ConfigDict(from_attributes=True)
