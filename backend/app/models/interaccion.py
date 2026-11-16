"""Entidades que el ER del informe no incluye pero que exigen los RF:
Favorito (RF-25), Reporte (RF-38), Notificacion (RF-37), Contacto (RF-40)
y la bitácora del RegistroAuditoriaObserver.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreadoMixin, IdMixin
from app.models.enums import (
    EstadoContacto,
    EstadoReporte,
    MotivoReporte,
    TipoContacto,
    TipoObjetoReporte,
)
from app.models.tipos import enum_col
from app.models.usuario import Usuario


class Favorito(IdMixin, CreadoMixin, Base):
    """Interfaz 'Favoritable' de la Fig. 11: guía, proveedor/tienda o evento.

    Tres FK opcionales y un CHECK que exige exactamente una: integridad
    referencial real sin perder el polimorfismo.
    """
    __tablename__ = "favorito"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(contenido_id, directorio_item_id, evento_id) = 1", name="exactamente_un_objeto"
        ),
        Index("uq_favorito_contenido", "usuario_id", "contenido_id", unique=True,
              postgresql_where="contenido_id IS NOT NULL"),
        Index("uq_favorito_directorio", "usuario_id", "directorio_item_id", unique=True,
              postgresql_where="directorio_item_id IS NOT NULL"),
        Index("uq_favorito_evento", "usuario_id", "evento_id", unique=True,
              postgresql_where="evento_id IS NOT NULL"),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    contenido_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contenido.id", ondelete="CASCADE")
    )
    directorio_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("directorio_item.id", ondelete="CASCADE")
    )
    evento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evento.id", ondelete="CASCADE")
    )


class Reporte(IdMixin, CreadoMixin, Base):
    __tablename__ = "reporte"
    __table_args__ = (Index("ix_reporte_objeto", "tipo_objeto", "objeto_id"),)

    reportante_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="SET NULL")
    )
    tipo_objeto: Mapped[TipoObjetoReporte] = mapped_column(enum_col(TipoObjetoReporte))
    objeto_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    motivo: Mapped[MotivoReporte] = mapped_column(enum_col(MotivoReporte))
    detalle: Mapped[str] = mapped_column(Text, default="")
    estado: Mapped[EstadoReporte] = mapped_column(
        enum_col(EstadoReporte), default=EstadoReporte.ABIERTO, index=True
    )
    resolucion: Mapped[str | None] = mapped_column(Text)
    resuelto_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="SET NULL")
    )
    resuelto_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    reportante: Mapped[Usuario | None] = relationship(foreign_keys=[reportante_id], lazy="joined")


class Notificacion(IdMixin, CreadoMixin, Base):
    __tablename__ = "notificacion"
    __table_args__ = (Index("ix_notificacion_usuario_leida", "usuario_id", "leida"),)

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE")
    )
    tipo: Mapped[str] = mapped_column(String(40))
    mensaje: Mapped[str] = mapped_column(String(400))
    enlace: Mapped[str | None] = mapped_column(String(300))
    leida: Mapped[bool] = mapped_column(Boolean, default=False)


class Contacto(IdMixin, CreadoMixin, Base):
    """Formulario de contacto (RF-40). No requiere sesión: lo usa también una cuenta suspendida."""
    __tablename__ = "contacto"

    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))
    tipo: Mapped[TipoContacto] = mapped_column(enum_col(TipoContacto))
    asunto: Mapped[str] = mapped_column(String(200))
    mensaje: Mapped[str] = mapped_column(Text)
    estado: Mapped[EstadoContacto] = mapped_column(enum_col(EstadoContacto), default=EstadoContacto.NUEVO)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="SET NULL")
    )


class RegistroAuditoria(IdMixin, CreadoMixin, Base):
    """Bitácora escrita por RegistroAuditoriaObserver."""
    __tablename__ = "registro_auditoria"

    evento: Mapped[str] = mapped_column(String(60), index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="SET NULL")
    )
    detalle: Mapped[dict] = mapped_column(JSONB, default=dict)
