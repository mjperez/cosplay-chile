"""Base declarativa de SQLAlchemy y utilidades comunes."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base de todos los modelos. Alembic lee `Base.metadata`."""


class ConMarcaDeTiempo:
    """Columnas de auditoría reutilizables."""

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def nuevo_uuid() -> uuid.UUID:
    """Identificador por defecto generado en Python.

    Se genera en el cliente y no con `gen_random_uuid()` para que el esquema
    no dependa de una extensión de PostgreSQL y las pruebas puedan correr
    sobre SQLite.
    """
    return uuid.uuid4()
