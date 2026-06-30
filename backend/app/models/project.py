from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type_research_id: Mapped[str | None] = mapped_column(
        ForeignKey("type_research.id"), nullable=True, index=True
    )
    design_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("design_type.id"), nullable=True, index=True
    )
    approach_id: Mapped[str | None] = mapped_column(
        ForeignKey("approach.id"), nullable=True, index=True
    )
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    faculty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    career: Mapped[str | None] = mapped_column(String(255), nullable=True)
    advisor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="projects")
    type_research: Mapped["TypeResearch | None"] = relationship(back_populates="projects")
    design_type: Mapped["DesignType | None"] = relationship(back_populates="projects")
    approach: Mapped["Approach | None"] = relationship(back_populates="projects")
    demographics: Mapped["ProjectDemographics | None"] = relationship(
        back_populates="project", uselist=False
    )

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
