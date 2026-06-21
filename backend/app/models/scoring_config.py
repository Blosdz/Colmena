from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ScoringConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "scoring_configs"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id"), nullable=False, index=True)
    instrument_id: Mapped[str | None] = mapped_column(ForeignKey("form_instruments.id"), nullable=True, index=True)
    dimension_id: Mapped[str | None] = mapped_column(ForeignKey("form_dimensions.id"), nullable=True, index=True)
    project_variable_id: Mapped[str | None] = mapped_column(ForeignKey("project_variables.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    scoring_level: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    aggregation_method: Mapped[str] = mapped_column(String(50), nullable=False, default="mean")
    missing_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="allow_partial")
    min_answered_items: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_completion_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    reverse_scoring_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    score_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    interpretation_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    project: Mapped["Project"] = relationship(back_populates="scoring_configs")
    form: Mapped["Form"] = relationship(back_populates="scoring_configs")
    instrument: Mapped["FormInstrument | None"] = relationship(back_populates="scoring_configs")
    dimension: Mapped["FormDimension | None"] = relationship(back_populates="scoring_configs")
    project_variable: Mapped["ProjectVariable | None"] = relationship(back_populates="scoring_configs")
    score_bands: Mapped[list["ScoreBand"]] = relationship(back_populates="scoring_config")
    response_scores: Mapped[list["ResponseScore"]] = relationship(back_populates="scoring_config")
