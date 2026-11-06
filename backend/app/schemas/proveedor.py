"""Esquemas del directorio de proveedores."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class ProveedorPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_proveedor: uuid.UUID
    nombre: str
    tipo: str
    region: str | None
    sitio_web: str | None
    contacto: str | None
    descripcion: str | None


class PaginaProveedores(BaseModel):
    total: int
    limite: int
    desplazamiento: int
    elementos: list[ProveedorPublico]
