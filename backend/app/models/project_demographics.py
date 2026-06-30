from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectDemographics(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Demografia de un proyecto (relacion 1:1 garantizada por el UNIQUE)."""

    __tablename__ = "project_demographics"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    population_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_size_planned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_size_current: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sampling_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    inclusion_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclusion_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="demographics")
