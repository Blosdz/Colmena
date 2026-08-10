from __future__ import annotations

from sqlalchemy import ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChartPalette(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chart_palettes"
    __table_args__ = (UniqueConstraint("form_id", "chart_key", name="uq_chart_palette_form_chart"),)

    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id"), nullable=False, index=True)
    chart_key: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    colors: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    form: Mapped["Form"] = relationship(back_populates="chart_palettes")
    project: Mapped["Project"] = relationship(back_populates="chart_palettes")
