from __future__ import annotations

from sqlalchemy import ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BaremoTableState(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tabla de baremo editada por el usuario en la vista de Resultados.

    ``table_key`` es el ``scoring_config_id`` para tablas derivadas de la
    resolucion automatica, o un uuid propio para tablas custom creadas a mano.
    ``rows_json`` guarda ``[{"category": str, "frequency": number}, ...]``;
    el porcentaje nunca se persiste porque siempre se deriva de las frecuencias.
    """

    __tablename__ = "baremo_table_states"
    __table_args__ = (UniqueConstraint("form_id", "table_key", name="uq_baremo_table_form_key"),)

    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    table_key: Mapped[str] = mapped_column(String(255), nullable=False)
    group_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="custom")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rows_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    form: Mapped["Form"] = relationship(back_populates="baremo_table_states")
    project: Mapped["Project"] = relationship(back_populates="baremo_table_states")
