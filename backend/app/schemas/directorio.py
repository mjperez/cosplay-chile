"""Esquemas de «dónde comprar» y de grupos de la comunidad."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class TiendaPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_tienda: uuid.UUID
    nombre: str
    tipo: str
    envia_a_chile: bool
    enlace_web: str | None = None
    region: str | None = None


class GrupoPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_comunidad: uuid.UUID
    nombre: str
    region: str | None = None
    plataforma: str
    enlace: str | None = None


class PaginaTiendas(BaseModel):
    total: int
    elementos: list[TiendaPublica]


class PaginaGrupos(BaseModel):
    total: int
    elementos: list[GrupoPublico]
