from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StudyType = Literal["ACADEMIC", "CENSO", "CUSTOM", "RESEARCH"]
StudyStatus = Literal["DRAFT", "OPEN", "CLOSED", "ARCHIVED"]


class StudyCreate(BaseModel):
    survey_id: int
    name: str = Field(min_length=1, max_length=255)
    study_type: StudyType
    start_at: datetime | None = None
    end_at: datetime | None = None
    min_publishable_n: int = Field(default=5, ge=1)
    settings: dict = Field(default_factory=dict)
    requires_invitation: bool = False
    analytics_plan: Literal["STANDARD", "ADVANCED", "PREMIUM"] = "STANDARD"


class StudyUpdate(BaseModel):
    name: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    min_publishable_n: int | None = Field(default=None, ge=1)
    barem_id: int | None = None
    settings: dict | None = None
    requires_invitation: bool | None = None


class StudyRead(BaseModel):
    id: int
    public_id: uuid.UUID
    project_id: int
    survey_id: int
    instrument_version_id: int | None
    analytics_plan_id: int | None = None
    analytics_plan_code: str | None = None
    instrument_id: int | None = None
    instrument_name: str | None = None
    instrument_version_code: str | None = None
    barem_id: int | None
    name: str
    study_type: str
    status: str
    start_at: datetime | None
    end_at: datetime | None
    min_publishable_n: int
    algorithm_version: str | None
    settings: dict
    requires_invitation: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudySnapshotRead(BaseModel):
    id: int
    study_id: int
    snapshot_type: str
    snapshot_data: dict
    sha256_hash: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StudyUnitTypeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=255)
    is_sensitive: bool = False
    sort_order: int | None = None
    metadata: dict = Field(default_factory=dict)


class StudyUnitTypeRead(StudyUnitTypeCreate):
    id: int
    study_id: int
    metadata: dict = Field(default_factory=dict, validation_alias="metadata_")

    model_config = ConfigDict(from_attributes=True)


class StudyUnitCreate(BaseModel):
    code: str | None = Field(default=None, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    parent_id: int | None = None
    is_active: bool = True
    metadata: dict = Field(default_factory=dict)


class StudyUnitRead(StudyUnitCreate):
    id: int
    study_unit_type_id: int
    metadata: dict = Field(default_factory=dict, validation_alias="metadata_")

    model_config = ConfigDict(from_attributes=True)


class ResponseSessionUnitsReplace(BaseModel):
    unit_ids: list[int] = Field(default_factory=list)


class ResponseSessionUnitsRead(BaseModel):
    response_session_id: int
    unit_ids: list[int]
