import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints, model_validator

from app.models.enums import EstadoPublicacion, Region, TipoEvento
from app.schemas.comun import AutorResumen, UrlExterna, UrlSegura


class EventoOut(BaseModel):
    id: uuid.UUID
    nombre: str
    descripcion: str
    tipo: TipoEvento
    fecha_inicio: date
    fecha_fin: date | None
    lugar: str
    comuna: str | None
    region: Region
    lat: float | None
    lng: float | None
    enlace_oficial: str | None
    imagen_url: str | None
    imagen_alt: str | None
    estado: EstadoPublicacion
    created_at: datetime
    sugerido_por: AutorResumen | None = None

    @classmethod
    def de(cls, e) -> "EventoOut":
        return cls(
            id=e.id, nombre=e.nombre, descripcion=e.descripcion, tipo=e.tipo, fecha_inicio=e.fecha_inicio,
            fecha_fin=e.fecha_fin, lugar=e.lugar, comuna=e.comuna, region=e.region, lat=e.lat, lng=e.lng,
            enlace_oficial=e.enlace_oficial, imagen_url=e.imagen_url, imagen_alt=e.imagen_alt, estado=e.estado,
            created_at=e.created_at, sugerido_por=AutorResumen.de(e.creado_por),
        )


class EventoDetalle(EventoOut):
    es_favorito: bool = False
    asistire: bool = False
    asistentes: int = 0


class EventoSugerido(BaseModel):
    """RF-17: los usuarios sugieren eventos; quedan pendientes de revisión."""
    nombre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]
    descripcion: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] = ""
    tipo: TipoEvento
    fecha_inicio: date
    fecha_fin: date | None = None
    lugar: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]
    comuna: Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)] | None = None
    region: Region
    enlace_oficial: UrlExterna | None = None
    imagen_url: UrlSegura | None = None
    imagen_alt: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] | None = None

    @model_validator(mode="after")
    def _fechas(self):
        if self.fecha_inicio < date.today():
            raise ValueError("La fecha de inicio no puede estar en el pasado")
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de término no puede ser anterior a la de inicio")
        if self.imagen_url and not self.imagen_alt:
            raise ValueError("Toda imagen necesita un texto alternativo")
        return self


class Asistencia(BaseModel):
    asistire: bool
    asistentes: int
