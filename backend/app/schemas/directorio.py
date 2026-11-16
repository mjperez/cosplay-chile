import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.models.enums import AlcanceTienda, Especialidad, Region, TipoDirectorio, TipoProducto
from app.schemas.comun import AutorResumen, ImagenRef, ModeloOrm, UrlExterna

Texto120 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]
Texto200 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]


class DirectorioResumen(BaseModel):
    id: uuid.UUID
    tipo: TipoDirectorio
    nombre: str
    descripcion: str
    region: Region | None
    comuna: str | None
    imagen_url: str | None
    imagen_alt: str | None
    especialidades: list[str] | None = None
    tipos_producto: list[str] | None = None
    alcance: AlcanceTienda | None = None
    envia_a_chile: bool | None = None
    tienda_fisica: bool | None = None
    plataforma: str | None = None
    precio_desde: int | None = None
    precio_hasta: int | None = None
    lat: float | None = None
    lng: float | None = None
    promedio: float | None = None
    total_resenas: int = 0

    @classmethod
    def de(cls, item, promedio=None, total=0) -> "DirectorioResumen":
        return cls(
            id=item.id, tipo=item.tipo, nombre=item.nombre, descripcion=item.descripcion, region=item.region,
            comuna=item.comuna, imagen_url=item.imagen_url, imagen_alt=item.imagen_alt,
            especialidades=item.especialidades, tipos_producto=item.tipos_producto, alcance=item.alcance,
            envia_a_chile=item.envia_a_chile, tienda_fisica=item.tienda_fisica, plataforma=item.plataforma,
            precio_desde=item.precio_desde, precio_hasta=item.precio_hasta, lat=item.lat, lng=item.lng,
            promedio=round(float(promedio), 2) if promedio is not None else None, total_resenas=total or 0,
        )


class ResenaOut(ModeloOrm):
    id: uuid.UUID
    calificacion: int
    comentario: str
    created_at: datetime
    autor: AutorResumen | None

    @classmethod
    def de(cls, r) -> "ResenaOut":
        return cls(id=r.id, calificacion=r.calificacion, comentario=r.comentario, created_at=r.created_at,
                   autor=AutorResumen.de(r.usuario))


class DirectorioDetalle(DirectorioResumen):
    servicios: list[str] | None = None
    portafolio: list[ImagenRef] | None = None
    contacto: str | None = None
    sitio_web: str | None = None
    direccion: str | None = None
    perfil_usuario_id: uuid.UUID | None = None
    resenas: list[ResenaOut] = []
    es_favorito: bool = False
    puede_resenar: bool = False
    ya_resenado: bool = False


class PuntoMapa(BaseModel):
    id: uuid.UUID
    tipo: TipoDirectorio
    nombre: str
    lat: float
    lng: float
    region: Region | None
    comuna: str | None
    detalle: str = ""


class ResenaIn(BaseModel):
    calificacion: int = Field(ge=1, le=5)
    comentario: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""


class MiFichaUpdate(BaseModel):
    """Datos de la ficha del directorio que completa el propio prestador o tienda (RF-32)."""
    nombre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=150)] | None = None
    descripcion: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] | None = None
    region: Region | None = None
    comuna: Texto120 | None = None
    direccion: Texto200 | None = None
    contacto: Texto200 | None = None
    sitio_web: UrlExterna | None = None
    servicios: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]] | None = Field(default=None, max_length=20)
    especialidades: list[Especialidad] | None = Field(default=None, max_length=7)
    precio_desde: int | None = Field(default=None, ge=0, le=10_000_000)
    precio_hasta: int | None = Field(default=None, ge=0, le=10_000_000)
    portafolio: list[ImagenRef] | None = Field(default=None, max_length=20)
    tipos_producto: list[TipoProducto] | None = Field(default=None, max_length=6)
    alcance: AlcanceTienda | None = None
    tienda_fisica: bool | None = None

    @model_validator(mode="after")
    def _rango_precios(self):
        if self.precio_desde is not None and self.precio_hasta is not None and self.precio_hasta < self.precio_desde:
            raise ValueError("El precio máximo no puede ser menor que el mínimo")
        return self
