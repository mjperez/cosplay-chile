"""Usuario y Perfil (Fig. 11: relación 1 a 1; Fig. 18: Usuario / PerfilCosplayer)."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreadoMixin, IdMixin
from app.models.enums import EstadoUsuario, Region, Rol, TipoPerfil
from app.models.tipos import enum_col


class Usuario(IdMixin, CreadoMixin, Base):
    __tablename__ = "usuario"

    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[Rol] = mapped_column(enum_col(Rol), default=Rol.USUARIO)
    estado: Mapped[EstadoUsuario] = mapped_column(enum_col(EstadoUsuario), default=EstadoUsuario.ACTIVO)
    motivo_suspension: Mapped[str | None] = mapped_column(Text)
    # RNF-11 / Ley 21.719: fecha del consentimiento explícito
    consentimiento_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # OWASP A07: contador de intentos fallidos y bloqueo temporal
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    perfil: Mapped["Perfil"] = relationship(
        back_populates="usuario", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def es_admin(self) -> bool:
        return self.rol == Rol.ADMIN


class Perfil(IdMixin, Base):
    __tablename__ = "perfil"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), unique=True
    )
    tipo_perfil: Mapped[TipoPerfil] = mapped_column(enum_col(TipoPerfil), default=TipoPerfil.COSPLAYER)
    biografia: Mapped[str | None] = mapped_column(Text)
    region: Mapped[Region | None] = mapped_column(enum_col(Region, 2), index=True)
    # [{"red": "Instagram", "url": "https://..."}]
    redes_sociales: Mapped[list] = mapped_column(JSONB, default=list)
    # [{"url": "/media/...", "alt": "..."}]
    portafolio: Mapped[list] = mapped_column(JSONB, default=list)
    especialidad: Mapped[str | None] = mapped_column(String(120))
    disponibilidad: Mapped[str | None] = mapped_column(String(120))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    # RF-10: el usuario elige si su perfil aparece en el directorio público (opt-in)
    perfil_publico: Mapped[bool] = mapped_column(Boolean, default=False)

    usuario: Mapped[Usuario] = relationship(back_populates="perfil")


class TokenRecuperacion(IdMixin, CreadoMixin, Base):
    """Token de un solo uso para restablecer contraseña (RF-09). Se guarda su hash."""
    __tablename__ = "token_recuperacion"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usado: Mapped[bool] = mapped_column(Boolean, default=False)
