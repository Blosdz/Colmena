from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PublicIdMixin, TimestampMixin
from app.models.types import BigIntPK, JSONVariant


class OptionSet(Base, PublicIdMixin):
    __tablename__ = "option_sets"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    instrument_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("instrument_versions.id", ondelete="CASCADE")
    )
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    code: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )

    instrument_version = relationship("InstrumentVersion", back_populates="option_sets")
    options: Mapped[list["OptionSetOption"]] = relationship(
        back_populates="option_set", cascade="all, delete-orphan", order_by="OptionSetOption.sort_order"
    )


class OptionSetOption(Base):
    __tablename__ = "option_set_options"
    __table_args__ = (UniqueConstraint("option_set_id", "raw_code"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    option_set_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("option_sets.id", ondelete="CASCADE"), nullable=False
    )
    raw_code: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    numeric_value: Mapped[float | None] = mapped_column(Numeric)
    sort_order: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )

    option_set: Mapped[OptionSet] = relationship(back_populates="options")
