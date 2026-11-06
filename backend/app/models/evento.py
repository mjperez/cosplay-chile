"""Eventos de cosplay y participación de usuarios."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ConMarcaDeTiempo, nuevo_uuid

TIPOS_EVENTO = ("convencion", "concurso", "feria", "taller", "otro")


class EventoCosplay(Base, ConMarcaDeTiempo):
    __tablename__ = "evento_cosplay"

    id_evento: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(
        Enum(*TIPOS_EVENTO, name="tipo_evento", native_enum=False),
        nullable=False,
        default="convencion",
    )
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lugar: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[str | None] = mapped_column(String(80))
    enlace_oficial: Mapped[str | None] = mapped_column(String(500))

    participaciones: Mapped[list[ParticipacionEvento]] = relationship(
        back_populates="evento", cascade="all, delete-orphan"
    )


class ParticipacionEvento(Base):
    """Vincula a un usuario con un evento en un personaje concreto."""

    __tablename__ = "participacion_evento"
    __table_args__ = (UniqueConstraint("id_usuario", "id_evento", name="uq_participacion_usuario_evento"),)

    id_participacion: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    id_usuario: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False
    )
    id_evento: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evento_cosplay.id_evento", ondelete="CASCADE"), nullable=False
    )
    personaje: Mapped[str | None] = mapped_column(String(120))

    evento: Mapped[EventoCosplay] = relationship(back_populates="participaciones")
