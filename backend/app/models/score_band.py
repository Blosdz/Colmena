from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ScoreBand(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "score_bands"

    scoring_config_id: Mapped[str] = mapped_column(ForeignKey("scoring_configs.id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    min_value: Mapped[float] = mapped_column(Float, nullable=False)
    max_value: Mapped[float] = mapped_column(Float, nullable=False)
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    color_hint: Mapped[str | None] = mapped_column(String(50), nullable=True)

    scoring_config: Mapped["ScoringConfig"] = relationship(back_populates="score_bands")
    response_scores: Mapped[list["ResponseScore"]] = relationship(back_populates="band")
