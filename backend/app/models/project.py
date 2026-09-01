from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PublicIdMixin, TimestampMixin
from app.models.types import BigIntPK, JSONVariant

PROJECT_TYPES = ("ACADEMIC", "CENSO", "CUSTOM", "RESEARCH")


class Project(Base, PublicIdMixin, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(f"project_type IN {PROJECT_TYPES}", name="ck_projects_project_type"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    organization_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("organizations.id")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, nullable=False, default=dict
    )

    variables: Mapped[list["Variable"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
    instruments: Mapped[list["Instrument"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_code: Mapped[str] = mapped_column(String(60), nullable=False)
    permissions: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
