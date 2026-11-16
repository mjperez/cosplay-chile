import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.schemas.comun import AutorResumen, UrlSegura

Credito = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Alt = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=300)]


class ImagenConCreditos(BaseModel):
    """RF-27: toda foto de cosplay lleva crédito al fotógrafo y al cosplayer."""
    imagen_url: UrlSegura | None = None
    imagen_alt: Alt | None = None
    credito_fotografo: Credito | None = None
    credito_cosplayer: Credito | None = None

    @model_validator(mode="after")
    def _creditos(self):
        if self.imagen_url:
            faltan = [n for n, v in (("texto alternativo", self.imagen_alt), ("crédito al fotógrafo", self.credito_fotografo),
                                     ("crédito al cosplayer", self.credito_cosplayer)) if not v]
            if faltan:
                raise ValueError("La foto necesita " + ", ".join(faltan))
        return self


class ForoOut(BaseModel):
    id: uuid.UUID
    titulo: str
    slug: str
    categoria: str
    temas: int = 0
    ultima_actividad: datetime | None = None


class TemaIn(ImagenConCreditos):
    titulo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=200)]
    contenido: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=10000)]


class TemaResumen(BaseModel):
    id: uuid.UUID
    titulo: str
    autor: AutorResumen | None
    created_at: datetime
    respuestas: int = 0
    tiene_imagen: bool = False
    foro_slug: str
    foro_titulo: str


class RespuestaOut(BaseModel):
    id: uuid.UUID
    contenido: str
    autor: AutorResumen | None
    created_at: datetime


class TemaDetalle(BaseModel):
    id: uuid.UUID
    titulo: str
    contenido: str
    autor: AutorResumen | None
    created_at: datetime
    foro: ForoOut
    imagen_url: str | None
    imagen_alt: str | None
    credito_fotografo: str | None
    credito_cosplayer: str | None
    oculto: bool = False
    respuestas: list[RespuestaOut] = []


class RespuestaIn(BaseModel):
    contenido: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=5000)]


class ParticipacionIn(ImagenConCreditos):
    titulo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=160)]
    descripcion: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] = ""
    imagen_url: UrlSegura


class ParticipacionOut(BaseModel):
    id: uuid.UUID
    titulo: str
    descripcion: str
    autor: AutorResumen | None
    imagen_url: str | None
    imagen_alt: str | None
    credito_fotografo: str | None
    credito_cosplayer: str | None
    created_at: datetime


class DesafioOut(BaseModel):
    id: uuid.UUID
    titulo: str
    descripcion: str
    mes: int
    anio: int
    abierto: bool
    ganador: AutorResumen | None = None
    participaciones: int = 0


class DesafioDetalle(DesafioOut):
    lista_participaciones: list[ParticipacionOut] = []
    ganador_participacion_id: uuid.UUID | None = None
    ya_participo: bool = False


class DesafioIn(BaseModel):
    titulo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=160)]
    descripcion: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=3000)]
    mes: int = Field(ge=1, le=12)
    anio: int = Field(ge=2024, le=2100)


class GanadorIn(BaseModel):
    participacion_id: uuid.UUID
