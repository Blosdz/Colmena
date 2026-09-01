from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import metadata_field

QuestionType = Literal[
    "SINGLE_CHOICE",
    "MULTIPLE_CHOICE",
    "LIKERT",
    "NUMBER",
    "TEXT",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "MATRIX",
    "RANKING",
]
ResearchRole = Literal["EXOGENOUS", "ENDOGENOUS", "MEDIATOR", "MODERATOR", "CONTROL"]


class OptionSetOptionInput(BaseModel):
    raw_code: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1)
    numeric_value: float | None = None
    sort_order: int | None = None
    is_active: bool = True


class OptionSetOptionRead(OptionSetOptionInput):
    id: int

    model_config = ConfigDict(from_attributes=True)


class OptionSetCreate(BaseModel):
    code: str | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    metadata: dict = Field(default_factory=dict)
    options: list[OptionSetOptionInput] = Field(default_factory=list)


class OptionSetUpdate(BaseModel):
    code: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    metadata: dict | None = None
    options: list[OptionSetOptionInput] | None = None


class OptionSetRead(BaseModel):
    id: int
    public_id: uuid.UUID
    owner_user_id: int | None
    code: str | None
    name: str
    description: str | None
    metadata: dict = metadata_field()
    options: list[OptionSetOptionRead]

    model_config = ConfigDict(from_attributes=True)


class QuestionCreate(BaseModel):
    code: str | None = None
    source_code: str | None = None
    question_text: str = Field(min_length=1)
    short_label: str | None = None
    question_type: QuestionType
    research_role: ResearchRole | None = None
    category: str | None = None
    option_set_id: int | None = None
    option_set: OptionSetCreate | None = None
    is_scored: bool = False
    is_required_default: bool = False
    sort_order: int | None = None
    validation_rules: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class QuestionUpdate(BaseModel):
    code: str | None = None
    source_code: str | None = None
    question_text: str | None = None
    short_label: str | None = None
    question_type: QuestionType | None = None
    research_role: ResearchRole | None = None
    category: str | None = None
    option_set_id: int | None = None
    is_scored: bool | None = None
    is_required_default: bool | None = None
    sort_order: int | None = None
    validation_rules: dict | None = None
    metadata: dict | None = None


class QuestionRead(BaseModel):
    id: int
    public_id: uuid.UUID
    instrument_version_id: int | None
    option_set_id: int | None
    code: str | None
    source_code: str | None
    question_text: str
    short_label: str | None
    question_type: str
    research_role: str | None
    category: str | None
    is_scored: bool
    is_required_default: bool
    sort_order: int | None
    validation_rules: dict
    metadata: dict = metadata_field()
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionBatchItem(BaseModel):
    id: int
    patch: QuestionUpdate


class QuestionBatchUpdate(BaseModel):
    items: list[QuestionBatchItem]
