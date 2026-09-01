import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.types import BigIntPK, JSONVariant

EXPORT_TYPES = ("CSV", "XLSX", "SPSS", "POWERBI", "JSON", "PARQUET")
DATASET_SHAPES = ("LONG", "WIDE", "AGGREGATED")


class Export(Base):
    __tablename__ = "exports"
    __table_args__ = (
        CheckConstraint(f"export_type IN {EXPORT_TYPES}", name="ck_exports_export_type"),
        CheckConstraint(f"dataset_shape IN {DATASET_SHAPES}", name="ck_exports_dataset_shape"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    study_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    requested_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    export_type: Mapped[str] = mapped_column(String(40), nullable=False)
    dataset_shape: Mapped[str] = mapped_column(String(20), nullable=False, default="LONG")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    filters: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    storage_path: Mapped[str | None] = mapped_column(Text)
    row_count: Mapped[int | None] = mapped_column(BigInteger)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
