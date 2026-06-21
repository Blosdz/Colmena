from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    research_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    design_type: Mapped[str | None] = mapped_column(String(150), nullable=True)
    approach: Mapped[str | None] = mapped_column(String(100), nullable=True)
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    faculty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    career: Mapped[str | None] = mapped_column(String(255), nullable=True)
    advisor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    population_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_size_planned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_size_current: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    variables: Mapped[list["ProjectVariable"]] = relationship(back_populates="project")
    forms: Mapped[list["Form"]] = relationship(back_populates="project")
    responses: Mapped[list["FormResponse"]] = relationship(back_populates="project")
    export_artifacts: Mapped[list["ExportArtifact"]] = relationship(back_populates="project")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="project")
    scoring_configs: Mapped[list["ScoringConfig"]] = relationship(back_populates="project")
    control_scales: Mapped[list["ControlScale"]] = relationship(back_populates="project")
    response_scores: Mapped[list["ResponseScore"]] = relationship(back_populates="project")
    response_control_flags: Mapped[list["ResponseControlFlag"]] = relationship(back_populates="project")
    chart_editor_states: Mapped[list["ChartEditorState"]] = relationship(back_populates="project")
