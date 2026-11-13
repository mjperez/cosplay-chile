"""Esquemas exclusivos del panel de administración.

Las entradas reutilizan los `Literal` de los modelos para que un valor fuera
de catálogo sea rechazado por Pydantic (422) antes de llegar a la base de
datos, igual que en el resto de la API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class ResumenAdmin(BaseModel):
    """Contadores para la portada del panel. Se calculan en una sola consulta por tabla."""

    usuarios: int
    usuarios_activos: int
    contenido_pendiente: int
    contenido_publicado: int
    contenido_rechazado: int
    eventos: int
    inscripciones: int
    temas: int
    temas_abiertos: int
    respuestas: int
    desafios: int
    tiendas: int
    grupos: int
    proveedores: int
    categorias: int
    generado_en: datetime


class EstadoUsuarioEntrada(BaseModel):
    activo: bool


class EstadoTemaEntrada(BaseModel):
    estado: Literal["abierto", "cerrado", "oculto"]


def _url_http(valor: str | None) -> str | None:
    """Solo se aceptan enlaces http(s): evita `javascript:` en los href del panel."""
    if valor is None or valor == "":
        return None
    texto = valor.strip()
    if urlparse(texto).scheme.lower() not in ("http", "https") or not urlparse(texto).netloc:
        raise ValueError("el enlace debe ser una URL http(s) completa")
    return texto


class TiendaEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    tipo: Literal["telas", "insumos", "pelucas", "impresion_3d", "otro"] = "insumos"
    envia_a_chile: bool = True
    enlace_web: str | None = Field(default=None, max_length=500)
    region: str | None = Field(default=None, max_length=80)

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, valor: str) -> str:
        return valor.strip()

    @field_validator("enlace_web")
    @classmethod
    def validar_enlace(cls, valor: str | None) -> str | None:
        return _url_http(valor)

    @field_validator("region")
    @classmethod
    def region_vacia(cls, valor: str | None) -> str | None:
        return valor.strip() or None if valor else None


class GrupoEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    region: str | None = Field(default=None, max_length=80)
    plataforma: Literal["facebook", "discord", "instagram", "whatsapp", "foro", "otro"] = "facebook"
    enlace: str | None = Field(default=None, max_length=500)

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, valor: str) -> str:
        return valor.strip()

    @field_validator("enlace")
    @classmethod
    def validar_enlace(cls, valor: str | None) -> str | None:
        return _url_http(valor)

    @field_validator("region")
    @classmethod
    def region_vacia(cls, valor: str | None) -> str | None:
        return valor.strip() or None if valor else None
