"""Registro de intentos de inicio de sesión.

Se guarda en base y no en memoria por dos razones: el bloqueo tiene que
sobrevivir a un reinicio del proceso, y con más de un worker de uvicorn un
diccionario en memoria daría un contador distinto en cada proceso.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, nuevo_uuid


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class IntentoLogin(Base):
    __tablename__ = "intento_login"
    __table_args__ = (Index("ix_intento_correo_fecha", "correo", "creado_en"),)

    id_intento: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=nuevo_uuid)
    correo: Mapped[str] = mapped_column(String(255), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(45))
    exitoso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # La marca se genera en Python, no con `now()` del motor: así el valor es
    # idéntico en PostgreSQL y en SQLite y las comparaciones de ventana no
    # dependen de la zona horaria de la sesión.
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=ahora_utc
    )
