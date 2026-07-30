from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Scale(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Catálogo de escalas de respuesta. project_id NULL = preset del sistema."""

    __tablename__ = "scales"

    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Significado metodológico: frecuencia | intensidad | acuerdo | dificultad | satisfaccion | personalizada
    scale_kind: Mapped[str] = mapped_column(String(30), nullable=False, default="personalizada")
    # Cómo se ve: radio | slider_line | stars | faces | nps
    render_style: Mapped[str] = mapped_column(String(30), nullable=False, default="radio")
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    options: Mapped[list["ScaleOption"]] = relationship(
        back_populates="scale",
        cascade="all, delete-orphan",
        order_by="ScaleOption.sort_order",
    )


class ScaleOption(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scale_options"

    scale_id: Mapped[str] = mapped_column(
        ForeignKey("scales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # El puntaje que se suma para el baremo.
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    scale: Mapped["Scale"] = relationship(back_populates="options")
