"""Contratos HTTP de notificaciones y bitácora de auditoría."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "PaginaAuditoria",
    "PaginaNotificaciones",
    "RegistroAuditoriaPublico",
    "NotificacionPublica",
    "ResumenNotificaciones",
]


class _DesdeOrm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class NotificacionPublica(_DesdeOrm):
    id_notificacion: uuid.UUID
    tipo: str
    titulo: str
    mensaje: str
    id_recurso: uuid.UUID | None
    leida: bool
    creado_en: datetime


class PaginaNotificaciones(BaseModel):
    total: int
    sin_leer: int
    limite: int
    desplazamiento: int
    elementos: list[NotificacionPublica]


class ResumenNotificaciones(BaseModel):
    """Para el indicador del encabezado, sin traer toda la lista."""

    sin_leer: int


class RegistroAuditoriaPublico(_DesdeOrm):
    id_registro: uuid.UUID
    ocurrido_en: datetime
    categoria: str
    tipo_evento: str
    correo_actor: str | None
    id_recurso: uuid.UUID | None
    detalle: dict | None
    ip_origen: str | None


class PaginaAuditoria(BaseModel):
    total: int
    limite: int = Field(ge=1)
    desplazamiento: int = Field(ge=0)
    elementos: list[RegistroAuditoriaPublico]
