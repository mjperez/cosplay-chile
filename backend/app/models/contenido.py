"""Contenido editorial con herencia de tabla unida.

El diagrama de clases declara `Contenido` como clase abstracta con tres
subclases. En la base se traduce a una tabla base `contenido` más una tabla
por subtipo que comparte la clave primaria. Esa forma evita columnas nulas
que solo aplican a un tipo y deja la creación a cargo de la fábrica de US-08.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ConMarcaDeTiempo, nuevo_uuid

NIVELES = ("basico", "intermedio", "avanzado")
ESTADOS_CONTENIDO = ("pendiente", "publicado", "rechazado")


class CategoriaContenido(Base):
    __tablename__ = "categoria_contenido"

    id_categoria: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)


class Contenido(Base, ConMarcaDeTiempo):
    """Base de guías, entrevistas y artículos."""

    __tablename__ = "contenido"

    id_contenido: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    id_autor: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False, index=True
    )
    id_categoria: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categoria_contenido.id_categoria", ondelete="SET NULL")
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    resumen: Mapped[str | None] = mapped_column(Text)
    # Cuerpo enriquecido en HTML saneado por el cliente. Se guarda como texto
    # y no como JSON porque es un documento, no una estructura de datos.
    cuerpo: Mapped[str | None] = mapped_column(Text)
    imagenes: Mapped[list | None] = mapped_column(JSON)
    video_url: Mapped[str | None] = mapped_column(String(500))
    nivel: Mapped[str] = mapped_column(
        Enum(*NIVELES, name="nivel_dificultad", native_enum=False),
        nullable=False,
        default="basico",
    )
    estado: Mapped[str] = mapped_column(
        Enum(*ESTADOS_CONTENIDO, name="estado_contenido", native_enum=False),
        nullable=False,
        default="pendiente",
        index=True,
    )
    fecha_publicacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tipo: Mapped[str] = mapped_column(String(20), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": tipo,
        "polymorphic_identity": "contenido",
    }

    categoria: Mapped[CategoriaContenido | None] = relationship()


class GuiaTutorial(Contenido):
    """Guía paso a paso publicada por un usuario.

    Además del contenido común, una guía documenta el personaje, las medidas,
    las técnicas empleadas, el presupuesto declarado y las advertencias de
    seguridad. Es lo que la distingue de un artículo en la vista pública.
    """

    __tablename__ = "guia_tutorial"

    id_contenido: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contenido.id_contenido", ondelete="CASCADE"), primary_key=True
    )
    pasos: Mapped[list | None] = mapped_column(JSON)
    materiales: Mapped[list | None] = mapped_column(JSON)
    personaje: Mapped[str | None] = mapped_column(String(120))
    # Lista de {parte, valor}: "pecho: 92 cm". Estructurada para poder
    # comparar medidas entre guías, no como texto libre.
    medidas: Mapped[list | None] = mapped_column(JSON)
    tecnicas: Mapped[list | None] = mapped_column(JSON)
    presupuesto: Mapped[str | None] = mapped_column(String(200))
    seguridad: Mapped[str | None] = mapped_column(Text)

    __mapper_args__ = {"polymorphic_identity": "guia"}


class Entrevista(Contenido):
    """Entrevista a un miembro de la comunidad."""

    __tablename__ = "entrevista"

    id_contenido: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contenido.id_contenido", ondelete="CASCADE"), primary_key=True
    )
    preguntas: Mapped[list | None] = mapped_column(JSON)
    respuestas: Mapped[list | None] = mapped_column(JSON)

    __mapper_args__ = {"polymorphic_identity": "entrevista"}


class Articulo(Contenido):
    """Artículo de blog o noticia."""

    __tablename__ = "articulo"

    id_contenido: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contenido.id_contenido", ondelete="CASCADE"), primary_key=True
    )
    enlaces: Mapped[list | None] = mapped_column(JSON)

    __mapper_args__ = {"polymorphic_identity": "articulo"}
