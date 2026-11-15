"""Notificaciones internas y bitácora de auditoría (patrón Observer, ES2).

Ambas tablas son el efecto observable del `GestorEventos`: cuando un servicio
emite un evento de dominio, tres observadores escriben aquí sin que el
controlador conozca a ninguno de ellos.

`bitacora_auditoria` no tiene clave foránea hacia `usuario` a propósito: un
registro de auditoría debe sobrevivir a la baja o eliminación de la cuenta que
lo originó (Ley 19.223 de delitos informáticos y control A.8.15 de ISO 27002).
En su lugar se guarda el correo del actor como texto, que es lo que necesita
una investigación posterior.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, Uuid, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, nuevo_uuid

__all__ = ["BitacoraAuditoria", "Notificacion"]


class Notificacion(Base):
    """Aviso interno dirigido a una cuenta (RF-37)."""

    __tablename__ = "notificacion"

    id_notificacion: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=nuevo_uuid
    )
    id_usuario: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"), index=True, nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    titulo: Mapped[str] = mapped_column(String(160), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    id_recurso: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    leida: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BitacoraAuditoria(Base):
    """Registro inmutable de eventos relevantes para seguridad."""

    __tablename__ = "bitacora_auditoria"

    id_registro: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=nuevo_uuid
    )
    ocurrido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    categoria: Mapped[str] = mapped_column(String(40), nullable=False)
    tipo_evento: Mapped[str] = mapped_column(String(60), nullable=False)
    id_actor: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    correo_actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    id_recurso: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    detalle: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_origen: Mapped[str | None] = mapped_column(String(45), nullable=True)
