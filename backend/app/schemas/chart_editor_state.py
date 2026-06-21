from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ChartEditorStateSave(BaseModel):
    storage_key: str
    graphs_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None


class ChartEditorStateRead(BaseModel):
    id: str
    storage_key: str
    form_id: str
    chart_id: str
    project_id: str
    graphs_json: dict[str, Any] | None
    metadata_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class ChartEditorStateListRead(BaseModel):
    form_id: str
    total: int
    items: list[ChartEditorStateRead]


class ChartEditorStateDeleteResponse(BaseModel):
    status: str
    chart_id: str
