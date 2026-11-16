"""Calendario de eventos (Fig. 11 Evento; Fig. 18 EventoCosplay y ParticipacionEvento)."""
import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreadoMixin, IdMixin
from app.models.enums import EstadoPublicacion, Region, TipoEvento
from app.models.tipos import enum_col
from app.models.usuario import Usuario


class Evento(IdMixin, CreadoMixin, Base):
    __tablename__ = "evento"
    __table_args__ = (Index("ix_evento_estado_fecha", "estado", "fecha_inicio"),)

    nombre: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    tipo: Mapped[TipoEvento] = mapped_column(enum_col(TipoEvento))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    lugar: Mapped[str] = mapped_column(String(200))
    comuna: Mapped[str | None] = mapped_column(String(80))
    region: Mapped[Region] = mapped_column(enum_col(Region, 2), index=True)
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    # RF-16: enlace a la organización oficial o venta de entradas (externa, sin venta propia)
    enlace_oficial: Mapped[str | None] = mapped_column(String(300))
    imagen_url: Mapped[str | None] = mapped_column(String(500))
    imagen_alt: Mapped[str | None] = mapped_column(String(300))
    # Los eventos sugeridos por usuarios (RF-17) nacen PENDIENTE
    estado: Mapped[EstadoPublicacion] = mapped_column(
        enum_col(EstadoPublicacion), default=EstadoPublicacion.PUBLICADO
    )
    creado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="SET NULL")
    )

    creado_por: Mapped[Usuario | None] = relationship(lazy="joined")


class ParticipacionEvento(IdMixin, CreadoMixin, Base):
    """'Asistiré' (Fig. 18 ParticipacionEvento)."""
    __tablename__ = "participacion_evento"
    __table_args__ = (UniqueConstraint("usuario_id", "evento_id", name="uq_participacion_evento"),)

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    evento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evento.id", ondelete="CASCADE"), index=True
    )
    rol: Mapped[str | None] = mapped_column(String(40))  # asistente, concursante, staff
    personaje: Mapped[str | None] = mapped_column(String(120))
