from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExportArtifact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "export_artifacts"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    form_id: Mapped[str | None] = mapped_column(
        ForeignKey("forms.id"),
        nullable=True,
        index=True,
    )
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="export_artifacts")
    form: Mapped["Form | None"] = relationship(back_populates="export_artifacts")
