"""Foro de la comunidad y desafíos mensuales."""

from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ConMarcaDeTiempo, nuevo_uuid

ESTADOS_FORO = ("abierto", "cerrado", "oculto")


class ForoTema(Base, ConMarcaDeTiempo):
    __tablename__ = "foro_tema"

    id_tema: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    id_creador: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    contenido: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(
        Enum(*ESTADOS_FORO, name="estado_foro", native_enum=False),
        nullable=False,
        default="abierto",
    )

    respuestas: Mapped[list[ForoRespuesta]] = relationship(
        back_populates="tema", cascade="all, delete-orphan"
    )


class ForoRespuesta(Base, ConMarcaDeTiempo):
    __tablename__ = "foro_respuesta"

    id_respuesta: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    id_tema: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("foro_tema.id_tema", ondelete="CASCADE"), nullable=False, index=True
    )
    id_usuario: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False
    )
    contenido: Mapped[str] = mapped_column(Text, nullable=False)

    tema: Mapped[ForoTema] = relationship(back_populates="respuestas")


class DesafioMensual(Base, ConMarcaDeTiempo):
    __tablename__ = "desafio_mensual"

    id_desafio: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    id_ganador: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuario.id_usuario", ondelete="SET NULL")
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    mes: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # YYYY-MM
