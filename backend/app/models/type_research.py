from __future__ import annotations

from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class TypeResearch(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Catalogo de tipos de investigacion (descriptiva, correlacional, ...)."""

    __tablename__ = "type_research"

    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    projects: Mapped[list["Project"]] = relationship(back_populates="type_research")
