from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Usuario de Colmena vinculado a una cuenta de AppThesis (cross-login).

    El enlace con AppThesis se guarda en ``appthesis_user_id`` (UUID de
    ``"AT".usuarios.id`` en thesis-backend). Si la cuenta aun no esta vinculada
    el valor es ``NULL`` (equivalente al ``?? 0`` del diseno original, ya que el
    id real de AppThesis es un UUID, no un entero). ``thesis_id`` guarda la
    tesis activa del estudiante en AppThesis para enlazar proyectos de Colmena.
    """

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    appthesis_user_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, unique=True, index=True
    )
    thesis_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    projects: Mapped[list["Project"]] = relationship(back_populates="owner")
