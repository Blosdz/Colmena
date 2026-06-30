from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CatalogRead(BaseModel):
    """Item de un catalogo (type_research / design_type / approach)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CatalogListResponse(BaseModel):
    items: list[CatalogRead]
    total: int
