from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PublicIdMixin
from app.models.types import BigIntPK, JSONVariant


class AuditLog(Base, PublicIdMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    project_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("projects.id"))
    study_id: Mapped[int | None] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(120))
    entity_id: Mapped[int | None] = mapped_column(BigInteger)
    before_data: Mapped[dict | None] = mapped_column(JSONVariant)
    after_data: Mapped[dict | None] = mapped_column(JSONVariant)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
