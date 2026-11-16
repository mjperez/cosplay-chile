"""Directorio (Fig. 11): DirectorioItem + ProveedorServicio, Tienda, ComunidadGrupo.

Atributos de Fig. 11 complementados con los del ER (Fig. 18): comuna, dirección,
sitio web, envía a Chile, activo. Coordenadas para el mapa (RF-12).
"""
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreadoMixin, IdMixin
from app.models.enums import AlcanceTienda, Region, TipoDirectorio
from app.models.tipos import enum_col
from app.models.usuario import Usuario


class DirectorioItem(IdMixin, CreadoMixin, Base):
    __tablename__ = "directorio_item"
    __table_args__ = (
        # Índice por región pedido en el informe (RNF-04, pág. 29)
        Index("ix_directorio_tipo_region", "tipo", "region"),
        Index("ix_directorio_especialidades", "especialidades", postgresql_using="gin"),
        Index("ix_directorio_tipos_producto", "tipos_producto", postgresql_using="gin"),
    )

    tipo: Mapped[TipoDirectorio] = mapped_column(enum_col(TipoDirectorio))
    nombre: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    region: Mapped[Region | None] = mapped_column(enum_col(Region, 2), index=True)
    comuna: Mapped[str | None] = mapped_column(String(80))
    direccion: Mapped[str | None] = mapped_column(String(200))
    contacto: Mapped[str | None] = mapped_column(String(200))
    sitio_web: Mapped[str | None] = mapped_column(String(300))
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    imagen_url: Mapped[str | None] = mapped_column(String(500))
    imagen_alt: Mapped[str | None] = mapped_column(String(300))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    # Ficha vinculada a una cuenta que activó su perfil público (RF-10); null = curada por admin
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="SET NULL"), unique=True
    )

    # ProveedorServicio
    servicios: Mapped[list | None] = mapped_column(JSONB)
    especialidades: Mapped[list | None] = mapped_column(JSONB)
    precio_desde: Mapped[int | None] = mapped_column(Integer)  # CLP
    precio_hasta: Mapped[int | None] = mapped_column(Integer)  # CLP
    portafolio: Mapped[list | None] = mapped_column(JSONB)  # [{"url","alt"}]

    # Tienda
    tipos_producto: Mapped[list | None] = mapped_column(JSONB)
    alcance: Mapped[AlcanceTienda | None] = mapped_column(enum_col(AlcanceTienda))
    envia_a_chile: Mapped[bool | None] = mapped_column(Boolean)
    tienda_fisica: Mapped[bool | None] = mapped_column(Boolean)

    # ComunidadGrupo
    plataforma: Mapped[str | None] = mapped_column(String(60))

    usuario: Mapped[Usuario | None] = relationship(lazy="joined")

    __mapper_args__ = {"polymorphic_on": "tipo", "polymorphic_abstract": True}


class ProveedorServicio(DirectorioItem):
    __mapper_args__ = {"polymorphic_identity": TipoDirectorio.PROVEEDOR}


class Tienda(DirectorioItem):
    __mapper_args__ = {"polymorphic_identity": TipoDirectorio.TIENDA}


class ComunidadGrupo(DirectorioItem):
    __mapper_args__ = {"polymorphic_identity": TipoDirectorio.COMUNIDAD}


class Resena(IdMixin, CreadoMixin, Base):
    """Reseña / calificación de un proveedor o tienda (RF-19). Solo con sesión."""
    __tablename__ = "resena"
    __table_args__ = (
        UniqueConstraint("usuario_id", "directorio_item_id", name="uq_resena_usuario_item"),
        CheckConstraint("calificacion BETWEEN 1 AND 5", name="calificacion_rango"),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    directorio_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("directorio_item.id", ondelete="CASCADE"), index=True
    )
    calificacion: Mapped[int] = mapped_column(SmallInteger)
    comentario: Mapped[str] = mapped_column(Text, default="")
    oculta: Mapped[bool] = mapped_column(Boolean, default=False)

    usuario: Mapped[Usuario] = relationship(lazy="joined")
