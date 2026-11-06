"""Consultas sobre el registro de intentos de login."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.intento_login import IntentoLogin


def registrar(
    sesion: Session, *, correo: str, ip: str | None, exitoso: bool
) -> IntentoLogin:
    intento = IntentoLogin(correo=correo.lower(), ip=ip, exitoso=exitoso)
    sesion.add(intento)
    sesion.flush()
    return intento


def contar_fallidos_desde(sesion: Session, correo: str, desde: datetime) -> int:
    consulta = (
        select(func.count())
        .select_from(IntentoLogin)
        .where(
            IntentoLogin.correo == correo.lower(),
            IntentoLogin.exitoso.is_(False),
            IntentoLogin.creado_en >= desde,
        )
    )
    return sesion.scalar(consulta) or 0


def primer_fallido_desde(sesion: Session, correo: str, desde: datetime) -> datetime | None:
    consulta = (
        select(func.min(IntentoLogin.creado_en))
        .where(
            IntentoLogin.correo == correo.lower(),
            IntentoLogin.exitoso.is_(False),
            IntentoLogin.creado_en >= desde,
        )
    )
    return sesion.scalar(consulta)


def borrar_fallidos(sesion: Session, correo: str) -> int:
    resultado = sesion.execute(
        delete(IntentoLogin).where(
            IntentoLogin.correo == correo.lower(),
            IntentoLogin.exitoso.is_(False),
        )
    )
    return resultado.rowcount or 0


def borrar_anteriores_a(sesion: Session, limite: datetime) -> int:
    resultado = sesion.execute(delete(IntentoLogin).where(IntentoLogin.creado_en < limite))
    return resultado.rowcount or 0
