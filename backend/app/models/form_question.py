from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class FormQuestion(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "form_questions"

    form_id: Mapped[str] = mapped_column(
        ForeignKey("forms.id"),
        nullable=False,
        index=True,
    )
    section_id: Mapped[str | None] = mapped_column(
        ForeignKey("form_sections.id"),
        nullable=True,
        index=True,
    )
    instrument_id: Mapped[str | None] = mapped_column(
        ForeignKey("form_instruments.id"),
        nullable=True,
        index=True,
    )
    dimension_id: Mapped[str | None] = mapped_column(
        ForeignKey("form_dimensions.id"),
        nullable=True,
        index=True,
    )
    project_variable_id: Mapped[str | None] = mapped_column(
        ForeignKey("project_variables.id"),
        nullable=True,
        index=True,
    )
    code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    question_role: Mapped[str] = mapped_column(String(50), nullable=False, default="item")
    measurement_level: Mapped[str] = mapped_column(String(50), nullable=False, default="ordinal")
    data_type: Mapped[str] = mapped_column(String(50), nullable=False, default="numeric")
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_scored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_reverse_scored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    min_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    validation_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    config_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    form: Mapped["Form"] = relationship(back_populates="questions")
    section: Mapped["FormSection | None"] = relationship(back_populates="questions")
    instrument: Mapped["FormInstrument | None"] = relationship(back_populates="questions")
    dimension: Mapped["FormDimension | None"] = relationship(back_populates="questions")
    project_variable: Mapped["ProjectVariable | None"] = relationship(back_populates="questions")
    options: Mapped[list["FormQuestionOption"]] = relationship(back_populates="question")
    answers: Mapped[list["FormAnswer"]] = relationship(back_populates="question")
