"""Esquemas del perfil público de cosplayer."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class PerfilEntrada(BaseModel):
    especialidad: str | None = Field(default=None, max_length=120)
    portafolio_url: str | None = Field(default=None, max_length=500)
    biografia: str | None = Field(default=None, max_length=2000)
    region: str | None = Field(default=None, max_length=80)


class PerfilPublico(BaseModel):
    id_usuario: uuid.UUID
    nombre: str
    rol: str
    region: str
    especialidad: str | None = None
    portafolio_url: str | None = None
    biografia: str | None = None
