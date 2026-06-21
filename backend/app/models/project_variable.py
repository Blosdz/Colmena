from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectVariable(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "project_variables"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    variable_role: Mapped[str] = mapped_column(String(50), nullable=False, default="main", index=True)
    measurement_level: Mapped[str] = mapped_column(String(50), nullable=False, default="ordinal")
    data_type: Mapped[str] = mapped_column(String(50), nullable=False, default="numeric")
    is_required_for_analysis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="variables")
    instruments: Mapped[list["FormInstrument"]] = relationship(back_populates="project_variable")
    questions: Mapped[list["FormQuestion"]] = relationship(back_populates="project_variable")
    scoring_configs: Mapped[list["ScoringConfig"]] = relationship(back_populates="project_variable")
    response_scores: Mapped[list["ResponseScore"]] = relationship(back_populates="project_variable")
