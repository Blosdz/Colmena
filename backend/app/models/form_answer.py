from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FormAnswer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "form_answers"

    response_id: Mapped[str] = mapped_column(
        ForeignKey("form_responses.id"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(
        ForeignKey("form_questions.id"),
        nullable=False,
        index=True,
    )
    option_id: Mapped[str | None] = mapped_column(
        ForeignKey("form_question_options.id"),
        nullable=True,
        index=True,
    )
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    value_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    score_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    response: Mapped["FormResponse"] = relationship(back_populates="answers")
    question: Mapped["FormQuestion"] = relationship(back_populates="answers")
    option: Mapped["FormQuestionOption | None"] = relationship(back_populates="answers")
