from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ResponseScore(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "response_scores"
    __table_args__ = (UniqueConstraint("response_id", "scoring_config_id", name="uq_response_score_config"),)

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id"), nullable=False, index=True)
    response_id: Mapped[str] = mapped_column(ForeignKey("form_responses.id"), nullable=False, index=True)
    scoring_config_id: Mapped[str] = mapped_column(ForeignKey("scoring_configs.id"), nullable=False, index=True)
    instrument_id: Mapped[str | None] = mapped_column(ForeignKey("form_instruments.id"), nullable=True, index=True)
    dimension_id: Mapped[str | None] = mapped_column(ForeignKey("form_dimensions.id"), nullable=True, index=True)
    project_variable_id: Mapped[str | None] = mapped_column(ForeignKey("project_variables.id"), nullable=True, index=True)
    raw_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    weighted_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    answered_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missing_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    band_id: Mapped[str | None] = mapped_column(ForeignKey("score_bands.id"), nullable=True, index=True)
    band_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    validity_status: Mapped[str] = mapped_column(String(20), nullable=False, default="valid")
    warnings_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="response_scores")
    form: Mapped["Form"] = relationship(back_populates="response_scores")
    response: Mapped["FormResponse"] = relationship(back_populates="scores")
    scoring_config: Mapped["ScoringConfig"] = relationship(back_populates="response_scores")
    instrument: Mapped["FormInstrument | None"] = relationship(back_populates="response_scores")
    dimension: Mapped["FormDimension | None"] = relationship(back_populates="response_scores")
    project_variable: Mapped["ProjectVariable | None"] = relationship(back_populates="response_scores")
    band: Mapped["ScoreBand | None"] = relationship(back_populates="response_scores")
