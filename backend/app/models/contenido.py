"""Contenidos educativos (Fig. 11): Contenido abstracta + GuiaTutorial, Entrevista, ArticuloTecnico.

Herencia de tabla única (single-table inheritance) con discriminador ``tipo``.
Cada subclase define ``validar()`` con sus reglas propias; la ContenidoFactory
(app/patterns/contenido_factory.py) decide qué subclase instanciar.
"""
import uuid
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreadoMixin, IdMixin
from app.models.enums import EstadoPublicacion, Nivel, TipoContenido
from app.models.tipos import enum_col
from app.models.usuario import Usuario


class ContenidoInvalido(ValueError):
    """Regla de negocio propia de un tipo de contenido no cumplida."""


class CategoriaContenido(IdMixin, Base):
    """Taxonomía temática (RF-04, RF-31). El nivel va en Contenido.nivel."""
    __tablename__ = "categoria_contenido"

    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    descripcion: Mapped[str] = mapped_column(Text, default="")


def _lista_textos(valor, campo: str) -> list[str]:
    if valor is None:
        return []
    if not isinstance(valor, list) or not all(isinstance(v, str) for v in valor):
        raise ContenidoInvalido(f"El campo '{campo}' debe ser una lista de textos")
    return [v.strip() for v in valor if v.strip()]


class Contenido(IdMixin, CreadoMixin, Base):
    __tablename__ = "contenido"
    __table_args__ = (Index("ix_contenido_estado_nivel", "estado", "nivel"),)

    tipo: Mapped[TipoContenido] = mapped_column(enum_col(TipoContenido), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text)
    cuerpo: Mapped[str] = mapped_column(Text, default="")
    nivel: Mapped[Nivel] = mapped_column(enum_col(Nivel))
    estado: Mapped[EstadoPublicacion] = mapped_column(
        enum_col(EstadoPublicacion), default=EstadoPublicacion.PENDIENTE, index=True
    )
    motivo_rechazo: Mapped[str | None] = mapped_column(Text)
    imagen_url: Mapped[str | None] = mapped_column(String(500))
    imagen_alt: Mapped[str | None] = mapped_column(String(300))
    video_url: Mapped[str | None] = mapped_column(String(500))  # RF-18: video embebido
    publicado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    categoria_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categoria_contenido.id"), index=True
    )
    autor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"), index=True)

    # Campos específicos de cada subclase (columnas JSONB de la tabla única)
    pasos: Mapped[list | None] = mapped_column(JSONB)
    materiales: Mapped[list | None] = mapped_column(JSONB)
    entrevistado: Mapped[str | None] = mapped_column(String(120))
    preguntas: Mapped[list | None] = mapped_column(JSONB)
    respuestas: Mapped[list | None] = mapped_column(JSONB)
    enlaces: Mapped[list | None] = mapped_column(JSONB)

    categoria: Mapped[CategoriaContenido] = relationship(lazy="joined")
    autor: Mapped[Usuario] = relationship(lazy="joined")

    __mapper_args__ = {"polymorphic_on": "tipo", "polymorphic_abstract": True}

    # --- comportamiento común -----------------------------------------
    def asignar_datos_comunes(self, datos: dict) -> None:
        for campo in ("titulo", "descripcion", "cuerpo", "nivel", "imagen_url", "imagen_alt", "video_url"):
            if campo in datos:
                setattr(self, campo, datos[campo])
        if not (self.titulo or "").strip():
            raise ContenidoInvalido("El título es obligatorio")
        if not (self.descripcion or "").strip():
            raise ContenidoInvalido("La descripción es obligatoria")
        if self.imagen_url and not (self.imagen_alt or "").strip():
            raise ContenidoInvalido("Toda imagen necesita un texto alternativo (accesibilidad)")

    def validar(self) -> None:  # pragma: no cover - abstracto
        raise NotImplementedError

    def cargar_datos_propios(self, datos: dict) -> None:  # pragma: no cover - abstracto
        raise NotImplementedError

    @property
    def tipo_legible(self) -> str:
        return {"GUIA": "Guía / tutorial", "ENTREVISTA": "Entrevista", "ARTICULO": "Artículo técnico"}[
            self.tipo.value if hasattr(self.tipo, "value") else self.tipo
        ]


class GuiaTutorial(Contenido):
    """Guía paso a paso: exige pasos ordenados y lista de materiales."""
    __mapper_args__ = {"polymorphic_identity": TipoContenido.GUIA}

    def cargar_datos_propios(self, datos: dict) -> None:
        self.pasos = _lista_textos(datos.get("pasos"), "pasos")
        self.materiales = _lista_textos(datos.get("materiales"), "materiales")

    def validar(self) -> None:
        if len(self.pasos or []) < 1:
            raise ContenidoInvalido("Una guía necesita al menos un paso")
        if len(self.materiales or []) < 1:
            raise ContenidoInvalido("Una guía necesita su lista de materiales")


class Entrevista(Contenido):
    """Entrevista: ficha de preguntas y respuestas pareadas."""
    __mapper_args__ = {"polymorphic_identity": TipoContenido.ENTREVISTA}

    def cargar_datos_propios(self, datos: dict) -> None:
        self.entrevistado = (datos.get("entrevistado") or "").strip() or None
        self.preguntas = _lista_textos(datos.get("preguntas"), "preguntas")
        self.respuestas = _lista_textos(datos.get("respuestas"), "respuestas")

    def validar(self) -> None:
        if not self.entrevistado:
            raise ContenidoInvalido("Indica a quién se entrevista")
        if len(self.preguntas or []) < 1:
            raise ContenidoInvalido("Una entrevista necesita al menos una pregunta")
        if len(self.preguntas or []) != len(self.respuestas or []):
            raise ContenidoInvalido("Cada pregunta debe tener su respuesta")


class ArticuloTecnico(Contenido):
    """Artículo técnico: incluye enlaces a documentación de referencia."""
    __mapper_args__ = {"polymorphic_identity": TipoContenido.ARTICULO}

    def cargar_datos_propios(self, datos: dict) -> None:
        self.enlaces = _lista_textos(datos.get("enlaces"), "enlaces")

    def validar(self) -> None:
        if len(self.enlaces or []) < 1:
            raise ContenidoInvalido("Un artículo técnico necesita al menos un enlace de referencia")
        for enlace in self.enlaces:
            partes = urlparse(enlace)
            if partes.scheme not in ("http", "https") or not partes.netloc:
                raise ContenidoInvalido(f"Enlace no válido: {enlace}")
