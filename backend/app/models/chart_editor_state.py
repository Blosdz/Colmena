from __future__ import annotations

from sqlalchemy import ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChartEditorState(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chart_editor_states"
    __table_args__ = (UniqueConstraint("form_id", "chart_id", name="uq_chart_editor_form_chart"),)

    storage_key: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id"), nullable=False, index=True)
    chart_id: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    graphs_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    form: Mapped["Form"] = relationship(back_populates="chart_editor_states")
    project: Mapped["Project"] = relationship(back_populates="chart_editor_states")
