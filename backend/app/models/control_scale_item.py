from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ControlScaleItem(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "control_scale_items"

    control_scale_id: Mapped[str] = mapped_column(ForeignKey("control_scales.id"), nullable=False, index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("form_questions.id"), nullable=False, index=True)
    expected_option_id: Mapped[str | None] = mapped_column(ForeignKey("form_question_options.id"), nullable=True, index=True)
    expected_value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    fail_if_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    pair_group: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    control_scale: Mapped["ControlScale"] = relationship(back_populates="items")
    question: Mapped["FormQuestion"] = relationship()
    expected_option: Mapped["FormQuestionOption | None"] = relationship()
