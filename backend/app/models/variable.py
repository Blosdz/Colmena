"""Tabla `variables` (harness §7).

No existe en `colmena_postgresql_schema.sql` — se añade en la migración 0001
siguiendo exactamente la forma descrita en el harness backend.

`study_id` referencia `colmena.studies`, tabla creada por el SQL portado pero
sin modelo ORM todavía (Fase 3). La FK real se declara en SQL crudo dentro de
la migración; aquí sólo se mapea la columna para no acoplar este modelo a un
`Study` que todavía no existe en el dominio Fase 1+2.
"""

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PublicIdMixin, TimestampMixin
from app.models.types import BigIntPK, JSONVariant

VARIABLE_TYPES = ("QUESTION", "DERIVED", "DEMOGRAPHIC", "EXOGENOUS", "CONSTRUCT_SCORE", "SYSTEM")
DATA_TYPES = ("INTEGER", "DECIMAL", "TEXT", "BOOLEAN", "DATE", "DATETIME", "CATEGORY")
MEASUREMENT_LEVELS = ("NOMINAL", "ORDINAL", "SCALE", "BINARY", "TEXT")
VARIABLE_ROLES = ("INDEPENDENT", "DEPENDENT", "CONTROL", "EXOGENOUS", "DESCRIPTIVE", "OUTCOME", "NONE")


class Variable(Base, PublicIdMixin, TimestampMixin):
    __tablename__ = "variables"
    __table_args__ = (
        UniqueConstraint("project_id", "code"),
        UniqueConstraint("project_id", "construct_id"),
        CheckConstraint(f"variable_type IN {VARIABLE_TYPES}", name="ck_variables_variable_type"),
        CheckConstraint(f"data_type IN {DATA_TYPES}", name="ck_variables_data_type"),
        CheckConstraint(
            f"measurement_level IN {MEASUREMENT_LEVELS}", name="ck_variables_measurement_level"
        ),
        CheckConstraint(f"role IN {VARIABLE_ROLES}", name="ck_variables_role"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    study_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    instrument_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("instrument_versions.id", ondelete="SET NULL")
    )
    question_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="SET NULL")
    )
    construct_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("constructs.id", ondelete="CASCADE")
    )
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str | None] = mapped_column(Text)
    variable_type: Mapped[str] = mapped_column(String(40), nullable=False)
    data_type: Mapped[str] = mapped_column(String(40), nullable=False)
    measurement_level: Mapped[str] = mapped_column(String(40), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="NONE")
    is_editable: Mapped[bool] = mapped_column(nullable=False, default=True)
    formula: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )

    project = relationship("Project", back_populates="variables")
    instrument_version = relationship("InstrumentVersion")
    question = relationship("Question")
    construct = relationship("Construct")
