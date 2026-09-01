from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.types import BigIntPK, JSONVariant


class AnalyticsPlan(Base):
    __tablename__ = "analytics_plans"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    tools: Mapped[list["AnalyticsPlanTool"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class StatisticalTool(Base):
    __tablename__ = "statistical_tools"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    min_sample_size: Mapped[int | None] = mapped_column(Integer)
    requires_groups: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_numeric: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_medium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    analysis_method_code: Mapped[str | None] = mapped_column(String(100))
    is_official: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    plans: Mapped[list["AnalyticsPlanTool"]] = relationship(
        back_populates="tool", cascade="all, delete-orphan"
    )


class AnalyticsPlanTool(Base):
    __tablename__ = "analytics_plan_tools"

    plan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("analytics_plans.id", ondelete="CASCADE"), primary_key=True
    )
    tool_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("statistical_tools.id", ondelete="CASCADE"), primary_key=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    configuration: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    plan: Mapped[AnalyticsPlan] = relationship(back_populates="tools")
    tool: Mapped[StatisticalTool] = relationship(back_populates="plans")


class OrganizationCollaboratorCode(Base):
    __tablename__ = "organization_collaborator_codes"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    code_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    created_by_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column()
