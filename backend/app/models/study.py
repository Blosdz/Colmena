from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PublicIdMixin, TimestampMixin
from app.models.types import BigIntPK, JSONVariant

STUDY_TYPES = ("ACADEMIC", "CENSO", "CUSTOM", "RESEARCH")
STUDY_STATUSES = ("DRAFT", "OPEN", "CLOSED", "ARCHIVED")


class Study(Base, PublicIdMixin, TimestampMixin):
    __tablename__ = "studies"
    __table_args__ = (
        CheckConstraint(f"study_type IN {STUDY_TYPES}", name="ck_studies_study_type"),
        CheckConstraint("min_publishable_n >= 1", name="ck_studies_min_publishable_n"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    survey_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("surveys.id"), nullable=False)
    instrument_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("instrument_versions.id")
    )
    analytics_plan_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("analytics_plans.id")
    )
    barem_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("barems.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    study_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    min_publishable_n: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    algorithm_version: Mapped[str | None] = mapped_column(String(100))
    settings: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    # E-17: opt-in. Cuando es True, `POST /public/studies/{public_id}/response-sessions`
    # exige un token de invitación de un solo uso (ver InvitationService).
    # Default False para no cambiar el comportamiento de ningún estudio existente.
    requires_invitation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    survey = relationship("Survey")
    instrument_version = relationship("InstrumentVersion")
    analytics_plan = relationship("AnalyticsPlan")
    snapshots: Mapped[list["StudySnapshot"]] = relationship(
        back_populates="study", cascade="all, delete-orphan"
    )

    @property
    def instrument_id(self) -> int | None:
        return self.instrument_version.instrument_id if self.instrument_version else None

    @property
    def instrument_name(self) -> str | None:
        if self.instrument_version is None or self.instrument_version.instrument is None:
            return None
        return self.instrument_version.instrument.name

    @property
    def instrument_version_code(self) -> str | None:
        return self.instrument_version.version_code if self.instrument_version else None

    @property
    def analytics_plan_code(self) -> str | None:
        return self.analytics_plan.code if self.analytics_plan else None


class StudySnapshot(Base):
    __tablename__ = "study_snapshots"
    __table_args__ = (UniqueConstraint("study_id", "snapshot_type", "sha256_hash"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    study_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_type: Mapped[str] = mapped_column(String(50), nullable=False)
    snapshot_data: Mapped[dict] = mapped_column(JSONVariant, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    study: Mapped[Study] = relationship(back_populates="snapshots")


class StudyUnitType(Base):
    __tablename__ = "study_unit_types"
    __table_args__ = (UniqueConstraint("study_id", "code"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    study_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )


class StudyUnit(Base):
    __tablename__ = "study_units"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    study_unit_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("study_unit_types.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("study_units.id", ondelete="SET NULL")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )
