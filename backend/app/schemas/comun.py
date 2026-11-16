"""Tipos reutilizables y validaciones transversales de entrada (RNF-06)."""
import math
from typing import Annotated, Generic, TypeVar
from urllib.parse import urlparse

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

T = TypeVar("T")


def _validar_url_segura(valor: str) -> str:
    """Acepta /media/... (archivos propios) o http(s)://. Bloquea javascript:, data:, etc."""
    valor = valor.strip()
    if valor.startswith("/media/") and ".." not in valor:
        return valor
    partes = urlparse(valor)
    if partes.scheme in ("http", "https") and partes.netloc:
        return valor
    raise ValueError("Debe ser un enlace http(s) válido")


def _validar_url_externa(valor: str) -> str:
    partes = urlparse(valor.strip())
    if partes.scheme in ("http", "https") and partes.netloc:
        return valor.strip()
    raise ValueError("Debe ser un enlace http(s) válido")


UrlSegura = Annotated[str, StringConstraints(max_length=500), AfterValidator(_validar_url_segura)]
UrlExterna = Annotated[str, StringConstraints(max_length=300), AfterValidator(_validar_url_externa)]
TextoCorto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
TextoLargo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)]
TextoOpcional = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]


class ModeloOrm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ImagenRef(BaseModel):
    url: UrlSegura
    alt: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=300)] = Field(
        description="Texto alternativo obligatorio (accesibilidad, RNF-03)"
    )


class RedSocial(BaseModel):
    red: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=40)]
    url: UrlExterna


class Mensaje(BaseModel):
    mensaje: str


class Pagina(BaseModel, Generic[T]):
    items: list[T]
    total: int
    pagina: int
    por_pagina: int
    paginas: int

    @classmethod
    def crear(cls, items: list, total: int, pagina: int, por_pagina: int) -> "Pagina":
        return cls(
            items=items,
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            paginas=max(1, math.ceil(total / por_pagina)) if por_pagina else 1,
        )


class AutorResumen(ModeloOrm):
    id: str
    nombre: str

    @classmethod
    def de(cls, usuario) -> "AutorResumen | None":
        if usuario is None:
            return None
        return cls(id=str(usuario.id), nombre=usuario.nombre)
