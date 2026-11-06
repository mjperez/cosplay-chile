"""Directorio de profesionales, tiendas y comunidades."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Enum, String, Text, Uuid, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ConMarcaDeTiempo, nuevo_uuid

TIPOS_PROVEEDOR = ("cosmaker", "sastre", "fotografo", "tienda", "organizador", "otro")
TIPOS_TIENDA = ("telas", "insumos", "pelucas", "impresion_3d", "otro")
PLATAFORMAS = ("facebook", "discord", "instagram", "whatsapp", "foro", "otro")


class Proveedor(Base, ConMarcaDeTiempo):
    """Profesional que ofrece servicios a la comunidad (cosmaker, sastre, fotógrafo)."""

    __tablename__ = "proveedor"

    id_proveedor: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(
        Enum(*TIPOS_PROVEEDOR, name="tipo_proveedor", native_enum=False),
        nullable=False,
        default="cosmaker",
    )
    # Opcional a propósito: no todas las cuentas de la comunidad declaran su
    # región, y el directorio debe poder mostrar ese hueco en vez de inventarlo.
    region: Mapped[str | None] = mapped_column(String(80), index=True)
    sitio_web: Mapped[str | None] = mapped_column(String(500))
    contacto: Mapped[str | None] = mapped_column(String(200))
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )


class DondeComprar(Base, ConMarcaDeTiempo):
    """Tienda de materiales, nacional o internacional."""

    __tablename__ = "donde_comprar"

    id_tienda: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(
        Enum(*TIPOS_TIENDA, name="tipo_tienda", native_enum=False),
        nullable=False,
        default="insumos",
    )
    envia_a_chile: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    enlace_web: Mapped[str | None] = mapped_column(String(500))
    region: Mapped[str | None] = mapped_column(String(80))


class ComunidadGrupo(Base, ConMarcaDeTiempo):
    """Grupo o servidor donde la comunidad se organiza fuera de la plataforma."""

    __tablename__ = "comunidad_grupo"

    id_comunidad: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    region: Mapped[str | None] = mapped_column(String(80), index=True)
    plataforma: Mapped[str] = mapped_column(
        Enum(*PLATAFORMAS, name="plataforma_comunidad", native_enum=False),
        nullable=False,
        default="facebook",
    )
    enlace: Mapped[str | None] = mapped_column(String(500))
