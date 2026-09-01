import datetime as dt
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.types import BigIntPK, JSONVariant


class ActionPlan(Base, TimestampMixin):
    __tablename__ = "action_plans"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    study_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    approved_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )

    items: Mapped[list["ActionPlanItem"]] = relationship(
        back_populates="action_plan", cascade="all, delete-orphan"
    )


class ActionPlanItem(Base, TimestampMixin):
    __tablename__ = "action_plan_items"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    action_plan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("action_plans.id", ondelete="CASCADE"), nullable=False
    )
    construct_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("constructs.id"))
    analysis_run_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("analysis_runs.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    finding: Mapped[str | None] = mapped_column(Text)
    origin_hypothesis: Mapped[str | None] = mapped_column(Text)
    action_description: Mapped[str] = mapped_column(Text, nullable=False)
    responsible_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    responsible_label: Mapped[str | None] = mapped_column(String(255))
    priority: Mapped[int | None] = mapped_column(Integer)
    due_date: Mapped[dt.date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )

    action_plan: Mapped[ActionPlan] = relationship(back_populates="items")
    kpis: Mapped[list["Kpi"]] = relationship(back_populates="action_plan_item")


class Kpi(Base):
    __tablename__ = "kpis"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    action_plan_item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("action_plan_items.id", ondelete="CASCADE")
    )
    study_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    formula: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(80))
    baseline_value: Mapped[float | None] = mapped_column(Numeric)
    target_value: Mapped[float | None] = mapped_column(Numeric)
    frequency: Mapped[str | None] = mapped_column(String(80))
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    action_plan_item: Mapped[ActionPlanItem | None] = relationship(back_populates="kpis")
    measurements: Mapped[list["KpiMeasurement"]] = relationship(
        back_populates="kpi", cascade="all, delete-orphan"
    )


class KpiMeasurement(Base):
    __tablename__ = "kpi_measurements"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    kpi_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("kpis.id", ondelete="CASCADE"), nullable=False
    )
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    numeric_value: Mapped[float | None] = mapped_column(Numeric)
    text_value: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(30))
    source_reference: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    kpi: Mapped[Kpi] = relationship(back_populates="measurements")
