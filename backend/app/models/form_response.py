from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class FormResponse(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "form_responses"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    form_id: Mapped[str] = mapped_column(
        ForeignKey("forms.id"),
        nullable=False,
        index=True,
    )
    respondent_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="complete", index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="internal")
    metadata_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="responses")
    form: Mapped["Form"] = relationship(back_populates="responses")
    answers: Mapped[list["FormAnswer"]] = relationship(back_populates="response")
    scores: Mapped[list["ResponseScore"]] = relationship(back_populates="response")
    control_flags: Mapped[list["ResponseControlFlag"]] = relationship(back_populates="response")
