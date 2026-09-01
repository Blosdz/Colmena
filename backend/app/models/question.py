from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PublicIdMixin, TimestampMixin
from app.models.types import BigIntPK, JSONVariant

QUESTION_TYPES = (
    "SINGLE_CHOICE",
    "MULTIPLE_CHOICE",
    "LIKERT",
    "NUMBER",
    "TEXT",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "MATRIX",
    "RANKING",
)
# Rol de investigación (opcional): distinto del tipo de pregunta y de si el
# ítem participa en un scoring (`is_scored`). Muchas preguntas de un survey
# tipo CENSOPAS (edad, sexo, remuneración) no pertenecen a ninguna variable
# de investigación — por eso este campo es nullable y sin default forzado.
RESEARCH_ROLES = ("EXOGENOUS", "ENDOGENOUS", "MEDIATOR", "MODERATOR", "CONTROL")


class Question(Base, PublicIdMixin, TimestampMixin):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint(f"question_type IN {QUESTION_TYPES}", name="ck_questions_question_type"),
        CheckConstraint(
            f"research_role IS NULL OR research_role IN {RESEARCH_ROLES}",
            name="ck_questions_research_role",
        ),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    instrument_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("instrument_versions.id", ondelete="CASCADE")
    )
    created_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    option_set_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("option_sets.id"))
    code: Mapped[str | None] = mapped_column(String(100))
    source_code: Mapped[str | None] = mapped_column(String(100))
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    short_label: Mapped[str | None] = mapped_column(String(255))
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    research_role: Mapped[str | None] = mapped_column(String(30))
    category: Mapped[str | None] = mapped_column(String(100))
    is_scored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_required_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int | None] = mapped_column(Integer)
    validation_rules: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )

    instrument_version = relationship("InstrumentVersion", back_populates="questions")
    option_set = relationship("OptionSet")
    construct_links: Mapped[list["ConstructItem"]] = relationship(  # noqa: F821
        back_populates="question", cascade="all, delete-orphan"
    )
