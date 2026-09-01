import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.types import BigIntPK, JSONVariant


class AnalysisMethod(Base):
    __tablename__ = "analysis_methods"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    engine: Mapped[str] = mapped_column(String(50), nullable=False, default="PYTHON")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    study_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    analysis_method_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("analysis_methods.id")
    )
    requested_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    analysis_type: Mapped[str] = mapped_column(String(100), nullable=False)
    engine: Mapped[str] = mapped_column(String(50), nullable=False, default="PYTHON")
    engine_version: Mapped[str | None] = mapped_column(String(100))
    algorithm_version: Mapped[str | None] = mapped_column(String(100))
    parameters: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    input_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    results: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="analysis_run", cascade="all, delete-orphan"
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False
    )
    result_code: Mapped[str | None] = mapped_column(String(120))
    result_type: Mapped[str] = mapped_column(String(100), nullable=False)
    construct_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("constructs.id"))
    question_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("questions.id"))
    unit_type_id: Mapped[int | None] = mapped_column(BigInteger)
    unit_id: Mapped[int | None] = mapped_column(BigInteger)
    n_valid: Mapped[int | None] = mapped_column(Integer)
    numeric_value: Mapped[float | None] = mapped_column(Numeric)
    ci_lower: Mapped[float | None] = mapped_column(Numeric)
    ci_upper: Mapped[float | None] = mapped_column(Numeric)
    statistic_value: Mapped[float | None] = mapped_column(Numeric)
    degrees_freedom: Mapped[float | None] = mapped_column(Numeric)
    p_value: Mapped[float | None] = mapped_column(Numeric)
    adjusted_p_value: Mapped[float | None] = mapped_column(Numeric)
    effect_size: Mapped[float | None] = mapped_column(Numeric)
    effect_label: Mapped[str | None] = mapped_column(String(80))
    text_value: Mapped[str | None] = mapped_column(Text)
    result_data: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="results")
