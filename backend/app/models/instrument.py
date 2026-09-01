import datetime as dt

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PublicIdMixin, TimestampMixin
from app.models.types import BigIntPK, JSONVariant

# Estados válidos de instrument_version (harness §42): DRAFT, TEST, ACTIVE, USED, CLOSED, LOCKED.
INSTRUMENT_VERSION_STATUSES = ("DRAFT", "TEST", "ACTIVE", "USED", "CLOSED", "LOCKED")


class Instrument(Base, PublicIdMixin, TimestampMixin):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    organization_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("organizations.id")
    )
    code: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    instrument_type: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
    source_name: Mapped[str | None] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )

    versions: Mapped[list["InstrumentVersion"]] = relationship(
        back_populates="instrument", cascade="all, delete-orphan"
    )
    project = relationship("Project", back_populates="instruments")


class InstrumentVersion(Base, PublicIdMixin, TimestampMixin):
    __tablename__ = "instrument_versions"
    __table_args__ = (UniqueConstraint("instrument_id", "version_code"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    instrument_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False
    )
    version_code: Mapped[str] = mapped_column(String(80), nullable=False)
    version_name: Mapped[str | None] = mapped_column(String(255))
    edition: Mapped[str | None] = mapped_column(String(120))
    valid_from: Mapped[dt.date | None] = mapped_column(Date)
    valid_to: Mapped[dt.date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    scoring_status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="NOT_CONFIGURED"
    )
    instrument_kind: Mapped[str | None] = mapped_column(String(20))
    total_questions: Mapped[int | None] = mapped_column()
    psychosocial_questions: Mapped[int | None] = mapped_column()
    dimension_count: Mapped[int | None] = mapped_column()
    subdimension_count: Mapped[int] = mapped_column(nullable=False, default=0)
    source_reference: Mapped[str | None] = mapped_column(Text)
    config: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)

    instrument: Mapped[Instrument] = relationship(back_populates="versions")
    questions: Mapped[list["Question"]] = relationship(  # noqa: F821
        back_populates="instrument_version", cascade="all, delete-orphan"
    )
    constructs: Mapped[list["Construct"]] = relationship(  # noqa: F821
        back_populates="instrument_version", cascade="all, delete-orphan"
    )
    option_sets: Mapped[list["OptionSet"]] = relationship(  # noqa: F821
        back_populates="instrument_version", cascade="all, delete-orphan"
    )
