from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SurveyType = Literal["CUSTOM", "ACADEMIC", "CENSO", "INSTRUMENT"]


class SurveyCreate(BaseModel):
    created_by_user_id: int
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    survey_type: SurveyType = "CUSTOM"
    settings: dict = Field(default_factory=dict)


class SurveyFromInstrumentCreate(BaseModel):
    """harness §14: crear survey a partir de una versión de instrumento.

    El servicio crea relaciones `survey_questions` sin duplicar los ítems.
    """

    created_by_user_id: int
    instrument_version_id: int
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    survey_type: SurveyType = "INSTRUMENT"


class SurveyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    settings: dict | None = None


class SurveyRead(BaseModel):
    id: int
    public_id: uuid.UUID
    project_id: int
    instrument_version_id: int | None
    created_by_user_id: int
    name: str
    description: str | None
    survey_type: str
    status: str
    settings: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SurveyQuestionRead(BaseModel):
    survey_id: int
    question_id: int
    section_id: int | None
    sort_order: int
    is_required: bool | None
    display_text_override: str | None

    model_config = ConfigDict(from_attributes=True)
