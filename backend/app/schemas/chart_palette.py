from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class ChartPaletteSave(BaseModel):
    colors: list[str] = Field(min_length=1, max_length=200)

    @field_validator("colors")
    @classmethod
    def validate_colors(cls, value: list[str]) -> list[str]:
        for color in value:
            if not HEX_COLOR_RE.match(color):
                raise ValueError(f"Color inválido: {color!r} (se espera formato #RRGGBB)")
        return value


class ChartPaletteRead(BaseModel):
    id: str
    form_id: str
    chart_key: str
    project_id: str
    colors: list[str]
    created_at: datetime
    updated_at: datetime


class ChartPaletteDeleteResponse(BaseModel):
    status: str
    chart_key: str
