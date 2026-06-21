from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


CHART_IMAGE_FORMATS = {"png", "svg"}
CHART_IMAGE_SOURCE_TYPES = {"chart_editor", "chart_spec", "orchestrated", "manual"}


class ChartImageUploadRequest(BaseModel):
    chart_id: str | None = None
    chart_type: str | None = None
    title: str | None = None
    format: str
    data_url: str
    file_name: str | None = None
    source_type: str | None = None
    analysis_run_id: str | None = None
    metadata_json: dict[str, Any] | None = None

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in CHART_IMAGE_FORMATS:
            raise ValueError("invalid chart image format")
        return cleaned

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in CHART_IMAGE_SOURCE_TYPES:
            raise ValueError("invalid source_type")
        return cleaned


class ChartImageRead(BaseModel):
    artifact_id: str
    form_id: str
    project_id: str
    chart_id: str | None
    chart_type: str | None
    title: str | None
    format: str
    file_name: str
    file_path: str
    mime_type: str
    file_size_bytes: int
    created_at: datetime
    metadata_json: dict[str, Any] | None = None


class ChartImageListRead(BaseModel):
    form_id: str
    total: int
    items: list[ChartImageRead]


class ChartImageUploadResponse(BaseModel):
    status: str
    image: ChartImageRead
    message: str


class ChartImageDeleteResponse(BaseModel):
    status: str
    artifact_id: str
