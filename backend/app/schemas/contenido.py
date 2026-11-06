"""Esquemas del contenido editorial.

La entrada usa una unión discriminada por `tipo`: Pydantic elige el modelo
según ese campo y devuelve 422 si no coincide con ninguno. Así el rechazo de un
tipo desconocido no depende de un `if` escrito a mano en el endpoint.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal, Union
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

# Dominios aceptados para el video. Se valida el host, no la cadena completa:
# buscar "youtube.com" dentro de la URL daría por bueno "evil.com/?x=youtube.com".
DOMINIOS_VIDEO = ("youtube.com", "youtu.be", "vimeo.com", "tiktok.com")


class Medida(BaseModel):
    """Una medida del personaje o del traje, en pares parte/valor."""

    parte: str = Field(min_length=1, max_length=40)
    valor: str = Field(min_length=1, max_length=40)


class ContenidoBase(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    resumen: str | None = Field(default=None, max_length=500)
    nivel: Literal["basico", "intermedio", "avanzado"] = "basico"
    id_categoria: uuid.UUID | None = None
    cuerpo: str | None = Field(default=None, max_length=20000)
    imagenes: list[HttpUrl] | None = Field(default=None, max_length=10)
    video_url: str | None = Field(default=None, max_length=500)

    @field_validator("video_url")
    @classmethod
    def dominio_permitido(cls, valor: str | None) -> str | None:
        if not valor:
            return None
        host = (urlparse(valor).hostname or "").lower()
        if not host:
            raise ValueError("la URL del video no es válida")
        permitido = any(host == dominio or host.endswith(f".{dominio}") for dominio in DOMINIOS_VIDEO)
        if not permitido:
            raise ValueError(
                "el video tiene que estar en " + ", ".join(DOMINIOS_VIDEO)
            )
        return valor


class GuiaEntrada(ContenidoBase):
    tipo: Literal["guia"]
    personaje: str | None = Field(default=None, max_length=120)
    medidas: list[Medida] | None = Field(default=None, max_length=20)
    tecnicas: list[str] | None = Field(default=None, max_length=20)
    presupuesto: str | None = Field(default=None, max_length=200)
    seguridad: str | None = Field(default=None, max_length=2000)
    pasos: list[str] | None = Field(default=None, max_length=40)
    materiales: list[str] | None = Field(default=None, max_length=60)


class EntrevistaEntrada(ContenidoBase):
    tipo: Literal["entrevista"]
    preguntas: list[str] | None = Field(default=None, max_length=30)
    respuestas: list[str] | None = Field(default=None, max_length=30)


class ArticuloEntrada(ContenidoBase):
    tipo: Literal["articulo"]
    enlaces: list[HttpUrl] | None = Field(default=None, max_length=20)


ContenidoEntrada = Annotated[
    Union[GuiaEntrada, EntrevistaEntrada, ArticuloEntrada],
    Field(discriminator="tipo"),
]


class ContenidoPublico(BaseModel):
    """Vista plana: los campos que no aplican al tipo llegan en null."""

    model_config = ConfigDict(from_attributes=True)

    id_contenido: uuid.UUID
    tipo: str
    titulo: str
    resumen: str | None = None
    nivel: str
    estado: str
    cuerpo: str | None = None
    imagenes: list[str] | None = None
    video_url: str | None = None
    id_categoria: uuid.UUID | None = None
    fecha_publicacion: datetime | None = None
    creado_en: datetime

    # Solo guía
    personaje: str | None = None
    medidas: list[dict] | None = None
    tecnicas: list[str] | None = None
    presupuesto: str | None = None
    seguridad: str | None = None
    pasos: list[str] | None = None
    materiales: list[str] | None = None

    # Solo entrevista
    preguntas: list[str] | None = None
    respuestas: list[str] | None = None

    # Solo artículo
    enlaces: list[str] | None = None


class PaginaContenido(BaseModel):
    total: int
    limite: int
    desplazamiento: int
    elementos: list[ContenidoPublico]


class CategoriaPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_categoria: uuid.UUID
    nombre: str
    descripcion: str | None = None


class CategoriaEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    descripcion: str | None = Field(default=None, max_length=500)
