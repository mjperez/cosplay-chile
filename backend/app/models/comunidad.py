"""Comunidad (Fig. 11): Foro -> Tema -> Respuesta (composición) y DesafioMensual (Fig. 18)."""
import uuid

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreadoMixin, IdMixin
from app.models.usuario import Usuario


class Foro(IdMixin, Base):
    __tablename__ = "foro"

    titulo: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    categoria: Mapped[str] = mapped_column(String(300))  # descripción de la temática
    orden: Mapped[int] = mapped_column(SmallInteger, default=0)


class ImagenConCreditosMixin:
    """RF-27: fotos de cosplay con crédito al fotógrafo y al cosplayer."""
    imagen_url: Mapped[str | None] = mapped_column(String(500))
    imagen_alt: Mapped[str | None] = mapped_column(String(300))
    credito_fotografo: Mapped[str | None] = mapped_column(String(120))
    credito_cosplayer: Mapped[str | None] = mapped_column(String(120))


class Tema(IdMixin, CreadoMixin, ImagenConCreditosMixin, Base):
    __tablename__ = "tema"

    foro_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("foro.id", ondelete="CASCADE"), index=True
    )
    autor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    contenido: Mapped[str] = mapped_column(Text)
    oculto: Mapped[bool] = mapped_column(Boolean, default=False)

    autor: Mapped[Usuario] = relationship(lazy="joined")
    foro: Mapped[Foro] = relationship(lazy="joined")


class Respuesta(IdMixin, CreadoMixin, Base):
    __tablename__ = "respuesta"

    tema_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tema.id", ondelete="CASCADE"), index=True
    )
    autor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"), index=True)
    contenido: Mapped[str] = mapped_column(Text)
    oculto: Mapped[bool] = mapped_column(Boolean, default=False)

    autor: Mapped[Usuario] = relationship(lazy="joined")


class DesafioMensual(IdMixin, CreadoMixin, Base):
    """RF-36 (Fig. 18 DesafioMensual: título, mes, año, ganador)."""
    __tablename__ = "desafio_mensual"
    __table_args__ = (UniqueConstraint("mes", "anio", name="uq_desafio_mes_anio"),)

    titulo: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[str] = mapped_column(Text)
    mes: Mapped[int] = mapped_column(SmallInteger)
    anio: Mapped[int] = mapped_column(SmallInteger)
    ganador_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="SET NULL")
    )

    ganador: Mapped[Usuario | None] = relationship(lazy="joined")


class ParticipacionDesafio(IdMixin, CreadoMixin, ImagenConCreditosMixin, Base):
    """'1 Usuario puede participar en muchos Desafíos Mensuales' (nota Fig. 18)."""
    __tablename__ = "participacion_desafio"
    __table_args__ = (UniqueConstraint("desafio_id", "usuario_id", name="uq_participacion_desafio"),)

    desafio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("desafio_mensual.id", ondelete="CASCADE"), index=True
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    titulo: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    oculto: Mapped[bool] = mapped_column(Boolean, default=False)

    usuario: Mapped[Usuario] = relationship(lazy="joined")
