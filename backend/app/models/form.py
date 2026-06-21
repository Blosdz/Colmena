from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Form(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "forms"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    public_slug: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    allow_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    collect_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collect_closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    thank_you_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="forms")
    sections: Mapped[list["FormSection"]] = relationship(back_populates="form")
    instruments: Mapped[list["FormInstrument"]] = relationship(back_populates="form")
    questions: Mapped[list["FormQuestion"]] = relationship(back_populates="form")
    responses: Mapped[list["FormResponse"]] = relationship(back_populates="form")
    export_artifacts: Mapped[list["ExportArtifact"]] = relationship(back_populates="form")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="form")
    scoring_configs: Mapped[list["ScoringConfig"]] = relationship(back_populates="form")
    control_scales: Mapped[list["ControlScale"]] = relationship(back_populates="form")
    response_scores: Mapped[list["ResponseScore"]] = relationship(back_populates="form")
    response_control_flags: Mapped[list["ResponseControlFlag"]] = relationship(back_populates="form")
    chart_editor_states: Mapped[list["ChartEditorState"]] = relationship(back_populates="form")
