import datetime as dt
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PublicIdMixin
from app.models.types import BigIntPK, JSONVariant

RESPONSE_SESSION_STATUSES = ("STARTED", "IN_PROGRESS", "COMPLETED", "ABANDONED")
VALIDATION_STATUSES = ("PENDING", "VALID", "REVIEW", "EXCLUDED")


class ResponseSession(Base, PublicIdMixin):
    __tablename__ = "response_sessions"
    __table_args__ = (
        UniqueConstraint("study_id", "anonymous_token"),
        CheckConstraint(
            "completion_pct IS NULL OR (completion_pct >= 0 AND completion_pct <= 100)",
            name="ck_response_sessions_completion_pct",
        ),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    study_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    anonymous_token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, default=uuid.uuid4
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="STARTED")
    validation_status: Mapped[str | None] = mapped_column(String(30), default="PENDING")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    completion_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    exclusion_reason: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )

    responses: Mapped[list["Response"]] = relationship(
        back_populates="response_session", cascade="all, delete-orphan"
    )


class ResponseSessionUnit(Base):
    __tablename__ = "response_session_units"

    response_session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("response_sessions.id", ondelete="CASCADE"), primary_key=True
    )
    study_unit_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("study_units.id", ondelete="CASCADE"), primary_key=True
    )


class Response(Base):
    __tablename__ = "responses"
    __table_args__ = (UniqueConstraint("response_session_id", "question_id"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    study_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    response_session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("response_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    option_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("option_set_options.id")
    )
    raw_code: Mapped[str | None] = mapped_column(String(150))
    numeric_value: Mapped[float | None] = mapped_column(Numeric)
    text_value: Mapped[str | None] = mapped_column(Text)
    boolean_value: Mapped[bool | None] = mapped_column(Boolean)
    date_value: Mapped[dt.date | None] = mapped_column(Date)
    datetime_value: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    value_jsonb: Mapped[dict | None] = mapped_column(JSONVariant)
    is_missing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )

    response_session: Mapped[ResponseSession] = relationship(back_populates="responses")
    question = relationship("Question")
    option = relationship("OptionSetOption")


class ResponseSelectedOption(Base):
    __tablename__ = "response_selected_options"

    response_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("responses.id", ondelete="CASCADE"), primary_key=True
    )
    option_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("option_set_options.id"), primary_key=True
    )
