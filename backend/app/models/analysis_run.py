from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, utc_now


class AnalysisRun(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "analysis_runs"

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
    analysis_type: Mapped[str] = mapped_column(String(100), nullable=False, default="descriptive")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    params_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    result_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    project: Mapped["Project"] = relationship(back_populates="analysis_runs")
    form: Mapped["Form"] = relationship(back_populates="analysis_runs")
