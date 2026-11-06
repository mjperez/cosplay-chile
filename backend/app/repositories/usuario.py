"""Consultas de usuarios. El SQL vive aquí, no en los endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.usuario import Usuario


def obtener_por_correo(sesion: Session, correo: str) -> Usuario | None:
    return sesion.scalar(select(Usuario).where(func.lower(Usuario.correo) == correo.lower()))


def obtener_por_id(sesion: Session, id_usuario: uuid.UUID) -> Usuario | None:
    return sesion.get(Usuario, id_usuario)


def crear(
    sesion: Session,
    *,
    nombre: str,
    correo: str,
    password_hash: str,
    rol: str,
    region: str,
    consentimiento_fecha: datetime,
    consentimiento_version: str,
) -> Usuario:
    usuario = Usuario(
        nombre=nombre,
        correo=correo.lower(),
        password_hash=password_hash,
        rol=rol,
        region=region,
        consentimiento_fecha=consentimiento_fecha,
        consentimiento_version=consentimiento_version,
    )
    sesion.add(usuario)
    sesion.flush()
    return usuario


def contar(sesion: Session) -> int:
    return sesion.scalar(select(func.count()).select_from(Usuario)) or 0


def listar(sesion: Session, *, limite: int, desplazamiento: int) -> list[Usuario]:
    consulta = (
        select(Usuario)
        .order_by(Usuario.creado_en.desc())
        .limit(limite)
        .offset(desplazamiento)
    )
    return list(sesion.scalars(consulta))
