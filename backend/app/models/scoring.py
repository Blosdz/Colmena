"""Modelo de `scoring_rules` (harness §7 tabla, §26 CENSOPAS §27-30).

No se usa activamente en Fase 1+2 (el motor de scoring es Fase 6), pero el
clonado de instrumento (§13) debe copiar `scoring_rules` junto con
questions/constructs, así que el modelo debe existir para que la relación
sea consultable desde `InstrumentService.clone_version`.
"""

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PublicIdMixin, TimestampMixin
from app.models.types import BigIntPK, JSONVariant


class ScoringRule(Base, PublicIdMixin, TimestampMixin):
    __tablename__ = "scoring_rules"
    __table_args__ = (
        CheckConstraint(
            "question_id IS NOT NULL OR construct_id IS NOT NULL",
            name="ck_scoring_rules_target",
        ),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    instrument_version_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("instrument_versions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="CASCADE")
    )
    construct_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("constructs.id", ondelete="CASCADE")
    )
    rule_code: Mapped[str | None] = mapped_column(String(100))
    rule_type: Mapped[str] = mapped_column(String(60), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    formula_expression: Mapped[str | None] = mapped_column(Text)
    source_reference: Mapped[str | None] = mapped_column(Text)
    rule_version: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="DRAFT")
