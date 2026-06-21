from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class FormDimension(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "form_dimensions"

    instrument_id: Mapped[str] = mapped_column(
        ForeignKey("form_instruments.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    instrument: Mapped["FormInstrument"] = relationship(back_populates="dimensions")
    questions: Mapped[list["FormQuestion"]] = relationship(back_populates="dimension")
    scoring_configs: Mapped[list["ScoringConfig"]] = relationship(back_populates="dimension")
    response_scores: Mapped[list["ResponseScore"]] = relationship(back_populates="dimension")
