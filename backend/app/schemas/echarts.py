from __future__ import annotations

from pydantic import BaseModel


class PaletteRead(BaseModel):
    colors: list[str]
