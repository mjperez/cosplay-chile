import re
import uuid
from datetime import datetime
from typing import Annotated
from urllib.parse import parse_qs, urlparse

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

from app.models.enums import EstadoPublicacion, Nivel, TipoContenido
from app.schemas.comun import AutorResumen, ModeloOrm, TextoCorto, UrlSegura

Item = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


def _validar_video(url: str) -> str:
    """RF-18: solo video embebible de YouTube o Vimeo."""
    if video_embed(url) is None:
        raise ValueError("El video debe ser un enlace de YouTube o Vimeo")
    return url


def video_embed(url: str | None) -> str | None:
    if not url:
        return None
    p = urlparse(url)
    host = (p.netloc or "").lower().removeprefix("www.").removeprefix("m.")
    vid = None
    if host == "youtu.be":
        vid = p.path.strip("/")
    elif host in ("youtube.com", "youtube-nocookie.com"):
        vid = parse_qs(p.query).get("v", [None])[0] or (p.path.split("/embed/")[1] if "/embed/" in p.path else None)
    if vid and re.fullmatch(r"[A-Za-z0-9_-]{6,20}", vid):
        return f"https://www.youtube-nocookie.com/embed/{vid}"
    if host == "vimeo.com" and re.fullmatch(r"/\d+", p.path or ""):
        return f"https://player.vimeo.com/video{p.path}"
    return None


class CategoriaOut(ModeloOrm):
    id: uuid.UUID
    nombre: str
    slug: str
    descripcion: str = ""


class ContenidoCrear(BaseModel):
    """Formulario de UC6: título, descripción, categoría y archivos multimedia."""
    tipo: TipoContenido = TipoContenido.GUIA
    titulo: TextoCorto
    descripcion: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=500)]
    cuerpo: Annotated[str, StringConstraints(strip_whitespace=True, max_length=20000)] = ""
    nivel: Nivel
    categoria_id: str = Field(description="Id de una categoría existente")
    imagen_url: UrlSegura | None = None
    imagen_alt: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] | None = None
    video_url: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500), AfterValidator(_validar_video)] | None = None
    # GuiaTutorial
    pasos: list[Item] | None = Field(default=None, max_length=50)
    materiales: list[Item] | None = Field(default=None, max_length=60)
    # Entrevista
    entrevistado: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    preguntas: list[Item] | None = Field(default=None, max_length=40)
    respuestas: list[Item] | None = Field(default=None, max_length=40)
    # ArticuloTecnico
    enlaces: list[Item] | None = Field(default=None, max_length=20)


class ContenidoResumen(ModeloOrm):
    id: uuid.UUID
    tipo: TipoContenido
    titulo: str
    descripcion: str
    nivel: Nivel
    estado: EstadoPublicacion
    categoria: CategoriaOut
    autor: AutorResumen | None
    imagen_url: str | None = None
    imagen_alt: str | None = None
    publicado_at: datetime | None = None
    created_at: datetime

    @classmethod
    def de(cls, c) -> "ContenidoResumen":
        return cls(
            id=c.id, tipo=c.tipo, titulo=c.titulo, descripcion=c.descripcion, nivel=c.nivel, estado=c.estado,
            categoria=CategoriaOut.model_validate(c.categoria), autor=AutorResumen.de(c.autor),
            imagen_url=c.imagen_url, imagen_alt=c.imagen_alt, publicado_at=c.publicado_at, created_at=c.created_at,
        )


class ContenidoDetalle(ContenidoResumen):
    cuerpo: str = ""
    video_url: str | None = None
    video_embed: str | None = None
    motivo_rechazo: str | None = None
    pasos: list[str] | None = None
    materiales: list[str] | None = None
    entrevistado: str | None = None
    preguntas: list[str] | None = None
    respuestas: list[str] | None = None
    enlaces: list[str] | None = None
    es_favorito: bool = False

    @classmethod
    def de(cls, c, es_favorito: bool = False) -> "ContenidoDetalle":
        base = ContenidoResumen.de(c).model_dump()
        return cls(
            **base, cuerpo=c.cuerpo or "", video_url=c.video_url, video_embed=video_embed(c.video_url),
            motivo_rechazo=c.motivo_rechazo, pasos=c.pasos, materiales=c.materiales, entrevistado=c.entrevistado,
            preguntas=c.preguntas, respuestas=c.respuestas, enlaces=c.enlaces, es_favorito=es_favorito,
        )


class ContenidoCreado(BaseModel):
    mensaje: str
    contenido: ContenidoDetalle


class Rechazo(BaseModel):
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=1000)]
