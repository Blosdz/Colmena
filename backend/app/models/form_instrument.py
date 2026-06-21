from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class FormInstrument(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "form_instruments"

    form_id: Mapped[str] = mapped_column(
        ForeignKey("forms.id"),
        nullable=False,
        index=True,
    )
    project_variable_id: Mapped[str | None] = mapped_column(
        ForeignKey("project_variables.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    acronym: Mapped[str | None] = mapped_column(String(50), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_scale_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scoring_method: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reverse_scoring_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    form: Mapped["Form"] = relationship(back_populates="instruments")
    project_variable: Mapped["ProjectVariable | None"] = relationship(back_populates="instruments")
    dimensions: Mapped[list["FormDimension"]] = relationship(back_populates="instrument")
    questions: Mapped[list["FormQuestion"]] = relationship(back_populates="instrument")
    scoring_configs: Mapped[list["ScoringConfig"]] = relationship(back_populates="instrument")
    control_scales: Mapped[list["ControlScale"]] = relationship(back_populates="instrument")
    response_scores: Mapped[list["ResponseScore"]] = relationship(back_populates="instrument")
