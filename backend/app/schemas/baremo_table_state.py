from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BaremoTableRow(BaseModel):
    category: str = ""
    frequency: float = Field(default=0, ge=0)


class BaremoTableStateSave(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    group_kind: str = Field(default="custom", pattern="^(variable|dimension|custom)$")
    rows: list[BaremoTableRow] = Field(default_factory=list)


class BaremoTableStateRead(BaseModel):
    id: str
    form_id: str
    project_id: str
    user_id: str | None
    table_key: str
    group_kind: str
    title: str
    rows: list[BaremoTableRow]
    created_at: datetime
    updated_at: datetime


class BaremoTableStateListRead(BaseModel):
    form_id: str
    total: int
    items: list[BaremoTableStateRead]


class BaremoTableStateDeleteResponse(BaseModel):
    status: str
    table_key: str
