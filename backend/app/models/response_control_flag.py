from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ResponseControlFlag(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "response_control_flags"
    __table_args__ = (UniqueConstraint("response_id", "control_scale_id", name="uq_response_control_scale"),)

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id"), nullable=False, index=True)
    response_id: Mapped[str] = mapped_column(ForeignKey("form_responses.id"), nullable=False, index=True)
    control_scale_id: Mapped[str] = mapped_column(ForeignKey("control_scales.id"), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    flag_status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="response_control_flags")
    form: Mapped["Form"] = relationship(back_populates="response_control_flags")
    response: Mapped["FormResponse"] = relationship(back_populates="control_flags")
    control_scale: Mapped["ControlScale"] = relationship(back_populates="response_flags")
