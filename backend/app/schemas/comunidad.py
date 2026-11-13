"""Esquemas del foro y de los desafíos mensuales."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CATEGORIAS_FORO = (
    "Armaduras y props",
    "Pelucas y maquillaje",
    "Costura y vestuario",
    "Presupuesto y compras",
    "Eventos y comunidad",
)


class TemaEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    categoria: str = Field(min_length=2, max_length=80)
    contenido: str = Field(min_length=5, max_length=20000)


class TemaPublico(BaseModel):
    id_tema: uuid.UUID
    id_creador: uuid.UUID
    titulo: str
    categoria: str
    contenido: str | None = None
    estado: Literal["abierto", "cerrado", "oculto"]
    nombre_autor: str
    total_respuestas: int = 0
    creado_en: datetime


class PaginaTemas(BaseModel):
    total: int
    limite: int
    desplazamiento: int
    elementos: list[TemaPublico]


class RespuestaEntrada(BaseModel):
    contenido: str = Field(min_length=1, max_length=5000)


class RespuestaPublica(BaseModel):
    id_respuesta: uuid.UUID
    id_tema: uuid.UUID
    contenido: str
    nombre_autor: str
    creado_en: datetime


class TemaDetalle(TemaPublico):
    respuestas: list[RespuestaPublica] = []


class DesafioEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    mes: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", examples=["2026-11"])


class GanadorEntrada(BaseModel):
    id_usuario: uuid.UUID


class DesafioPublico(BaseModel):
    id_desafio: uuid.UUID
    titulo: str
    mes: str
    id_ganador: uuid.UUID | None = None
    nombre_ganador: str | None = None
    creado_en: datetime


class PaginaDesafios(BaseModel):
    total: int
    elementos: list[DesafioPublico]
