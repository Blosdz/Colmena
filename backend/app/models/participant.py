"""Participantes e invitaciones (E-17, harness §12).

Regla absoluta (ya documentada en `migrations/versions/sql/0001_colmena_schema.sql`
§12): `response_sessions` nunca lleva `participant_id`. Una invitación sólo
autentica la *creación* de una sesión pública de un solo uso — al consumirse
se marca su propio `status`/`consumed_at`, sin guardar qué `response_session`
resultó, para no dejar un mapeo reversible participante -> contenido de
respuesta.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PublicIdMixin
from app.models.types import BigIntPK, JSONVariant

INVITATION_STATUSES = ("PENDING", "SENT", "CONSUMED", "EXPIRED", "REVOKED")


class Participant(Base, PublicIdMixin):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    study_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(150))
    last_name: Mapped[str | None] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(100))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONVariant, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StudyInvitation(Base):
    __tablename__ = "study_invitations"
    __table_args__ = (UniqueConstraint("study_id", "access_token_hash"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    study_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    participant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("participants.id", ondelete="CASCADE")
    )
    access_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONVariant, nullable=False, default=dict)

    participant = relationship("Participant")
