"""Esquemas de eventos y participaciones (US de calendario)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TIPOS_EVENTO = ("convencion", "concurso", "feria", "taller", "otro")


def _utc_naive(valor: datetime | None) -> datetime | None:
    """Canonicaliza las fechas a UTC sin zona.

    SQLite no conserva el offset y PostgreSQL interpreta un datetime naive en
    la zona del servidor. Guardar siempre UTC naive evita que la misma hora se
    lea distinta en pruebas y en producción.
    """
    if valor is None:
        return None
    if valor.tzinfo is not None:
        return valor.astimezone(timezone.utc).replace(tzinfo=None)
    return valor


class EventoEntrada(BaseModel):
    nombre: str = Field(min_length=3, max_length=200)
    tipo: Literal["convencion", "concurso", "feria", "taller", "otro"] = "convencion"
    fecha_inicio: datetime
    fecha_fin: datetime | None = None
    lugar: str = Field(min_length=2, max_length=200)
    region: str | None = Field(default=None, max_length=80)
    enlace_oficial: str | None = Field(default=None, max_length=500)

    @field_validator("fecha_inicio", "fecha_fin")
    @classmethod
    def normalizar_fecha(cls, valor: datetime | None) -> datetime | None:
        return _utc_naive(valor)

    @model_validator(mode="after")
    def validar_rango(self) -> "EventoEntrada":
        if self.fecha_fin is not None and self.fecha_fin < self.fecha_inicio:
            raise ValueError("la fecha de término no puede ser anterior al inicio")
        return self


class EventoPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_evento: uuid.UUID
    nombre: str
    tipo: str
    fecha_inicio: datetime
    fecha_fin: datetime | None = None
    lugar: str
    region: str | None = None
    enlace_oficial: str | None = None
    total_participantes: int = 0
    creado_en: datetime


class PaginaEventos(BaseModel):
    total: int
    limite: int
    desplazamiento: int
    elementos: list[EventoPublico]


class ListaEventos(BaseModel):
    total: int
    elementos: list[EventoPublico]


class ParticipacionEntrada(BaseModel):
    personaje: str | None = Field(default=None, max_length=120)


class ParticipacionPublica(BaseModel):
    id_participacion: uuid.UUID
    id_usuario: uuid.UUID
    id_evento: uuid.UUID
    personaje: str | None = None
    nombre_usuario: str


class PaginaParticipaciones(BaseModel):
    total: int
    elementos: list[ParticipacionPublica]
