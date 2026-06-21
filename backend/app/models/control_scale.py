from sqlalchemy import Boolean, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ControlScale(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "control_scales"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id"), nullable=False, index=True)
    instrument_id: Mapped[str | None] = mapped_column(ForeignKey("form_instruments.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    control_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    comparison_operator: Mapped[str | None] = mapped_column(String(10), nullable=True)
    flag_level: Mapped[str] = mapped_column(String(20), nullable=False, default="warning")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    project: Mapped["Project"] = relationship(back_populates="control_scales")
    form: Mapped["Form"] = relationship(back_populates="control_scales")
    instrument: Mapped["FormInstrument | None"] = relationship(back_populates="control_scales")
    items: Mapped[list["ControlScaleItem"]] = relationship(back_populates="control_scale")
    response_flags: Mapped[list["ResponseControlFlag"]] = relationship(back_populates="control_scale")
