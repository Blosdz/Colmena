from sqlalchemy import Boolean, ForeignKey, Integer, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FormPublicSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "form_public_snapshots"
    __table_args__ = (
        UniqueConstraint("form_id", "version", name="uq_form_public_snapshots_version"),
    )

    form_id: Mapped[str] = mapped_column(
        ForeignKey("forms.id"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
