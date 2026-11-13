"""Consultas del perfil público de cosplayer."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.usuario import PerfilCosplayer, Usuario


def obtener_usuario(sesion: Session, id_usuario: uuid.UUID) -> Usuario | None:
    return sesion.get(Usuario, id_usuario)


def perfil_de(sesion: Session, id_usuario: uuid.UUID) -> PerfilCosplayer | None:
    return sesion.scalar(
        select(PerfilCosplayer).where(PerfilCosplayer.id_usuario == id_usuario)
    )


def guardar(
    sesion: Session,
    *,
    id_usuario: uuid.UUID,
    especialidad: str | None,
    portafolio_url: str | None,
    biografia: str | None,
    region: str | None,
) -> PerfilCosplayer:
    """Alta o actualización: el perfil es único por usuario."""
    perfil = perfil_de(sesion, id_usuario)
    if perfil is None:
        perfil = PerfilCosplayer(id_usuario=id_usuario)
        sesion.add(perfil)
    perfil.especialidad = especialidad
    perfil.portafolio_url = portafolio_url
    perfil.biografia = biografia
    # `None` significa «no me enviaron este campo»: se conserva el valor
    # anterior. La cadena vacía sí es una decisión explícita de ocultar la
    # región, y se guarda como tal.
    if region is not None:
        perfil.region = region
    sesion.flush()
    return perfil
