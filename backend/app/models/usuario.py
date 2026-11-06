"""Modelos de usuario y perfil público."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, true
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ConMarcaDeTiempo, nuevo_uuid

ROLES = (
    "visitante",
    "cosplayer",
    "cosmaker",
    "sastre",
    "tienda",
    "fotografo",
    "organizador",
    "administrador",
)


class Usuario(Base, ConMarcaDeTiempo):
    """Cuenta de la plataforma.

    `password_hash` guarda el resultado de bcrypt o argon2, nunca la
    contraseña. `consentimiento_*` registra la aceptación de la política de
    privacidad con fecha y versión del texto, como exige la Ley 21.719.
    """

    __tablename__ = "usuario"

    id_usuario: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(
        Enum(*ROLES, name="rol_usuario", native_enum=False, validate_strings=True),
        nullable=False,
        default="cosplayer",
    )
    region: Mapped[str] = mapped_column(String(80), nullable=False)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    consentimiento_fecha: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consentimiento_version: Mapped[str | None] = mapped_column(String(20))

    perfil: Mapped[PerfilCosplayer | None] = relationship(
        back_populates="usuario", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"<Usuario {self.correo} ({self.rol})>"


class PerfilCosplayer(Base):
    """Datos públicos del cosplayer, separados de la cuenta."""

    __tablename__ = "perfil_cosplayer"

    id_perfil: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    id_usuario: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"), unique=True, nullable=False
    )
    especialidad: Mapped[str | None] = mapped_column(String(120))
    portafolio_url: Mapped[str | None] = mapped_column(String(500))
    biografia: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(String(80))

    usuario: Mapped[Usuario] = relationship(back_populates="perfil")
