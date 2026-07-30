from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCALE_KINDS = {"frecuencia", "intensidad", "acuerdo", "dificultad", "satisfaccion", "personalizada"}
RENDER_STYLES = {"radio", "slider_line", "stars", "faces", "nps"}


class ScaleOptionBase(BaseModel):
    value: int
    label: str = Field(..., min_length=1, max_length=120)
    sort_order: int = 0

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("label must not be empty")
        return cleaned


class ScaleOptionRead(ScaleOptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


class ScaleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    scale_kind: str = Field(default="personalizada", max_length=30)
    render_style: str = Field(default="radio", max_length=30)
    points: int = Field(default=5, ge=2, le=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned

    @field_validator("scale_kind")
    @classmethod
    def validate_kind(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in SCALE_KINDS:
            raise ValueError(f"scale_kind must be one of {sorted(SCALE_KINDS)}")
        return cleaned

    @field_validator("render_style")
    @classmethod
    def validate_render(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in RENDER_STYLES:
            raise ValueError(f"render_style must be one of {sorted(RENDER_STYLES)}")
        return cleaned


class ScaleCreate(ScaleBase):
    options: list[ScaleOptionBase] = Field(..., min_length=2)


class ScaleRead(ScaleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str | None
    options: list[ScaleOptionRead]
    created_at: datetime
    updated_at: datetime


class ScaleListResponse(BaseModel):
    items: list[ScaleRead]
    total: int
