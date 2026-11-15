"""Contrato HTTP de la subida de imágenes."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["ArchivoPublico"]


class ArchivoPublico(BaseModel):
    identificador: str
    enlace: str
    tipo_mime: str
    tamano: int = Field(ge=1)
