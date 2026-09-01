from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PublicIdMixin, TimestampMixin
from app.models.types import BigIntPK, JSONVariant

SURVEY_TYPES = ("CUSTOM", "ACADEMIC", "CENSO", "INSTRUMENT")


class Survey(Base, PublicIdMixin, TimestampMixin):
    __tablename__ = "surveys"
    __table_args__ = (
        CheckConstraint(f"survey_type IN {SURVEY_TYPES}", name="ck_surveys_survey_type"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    instrument_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("instrument_versions.id")
    )
    created_by_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    survey_type: Mapped[str] = mapped_column(String(40), nullable=False, default="CUSTOM")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    settings: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)

    sections: Mapped[list["SurveySection"]] = relationship(
        back_populates="survey", cascade="all, delete-orphan"
    )
    survey_questions: Mapped[list["SurveyQuestion"]] = relationship(
        back_populates="survey", cascade="all, delete-orphan"
    )
    instrument_version = relationship("InstrumentVersion")


class SurveySection(Base):
    __tablename__ = "survey_sections"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    survey_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    section_kind: Mapped[str] = mapped_column(String(30), nullable=False, default="INSTRUMENT")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    settings: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)

    survey: Mapped[Survey] = relationship(back_populates="sections")


class SurveyQuestion(Base):
    __tablename__ = "survey_questions"

    survey_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("surveys.id", ondelete="CASCADE"), primary_key=True
    )
    question_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("questions.id"), primary_key=True
    )
    section_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("survey_sections.id", ondelete="SET NULL")
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool | None] = mapped_column(Boolean)
    display_text_override: Mapped[str | None] = mapped_column(Text)
    settings: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)

    survey: Mapped[Survey] = relationship(back_populates="survey_questions")
    question = relationship("Question")
