"""Reglas de negocio del perfil público."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories import perfil as repo
from app.schemas.perfil import PerfilEntrada, PerfilPublico

__all__ = ["UsuarioNoEncontrado", "actualizar", "ver"]


class UsuarioNoEncontrado(Exception):
    pass


def ver(sesion: Session, id_usuario: uuid.UUID) -> PerfilPublico:
    usuario = repo.obtener_usuario(sesion, id_usuario)
    if usuario is None:
        raise UsuarioNoEncontrado(str(id_usuario))
    perfil = repo.perfil_de(sesion, id_usuario)
    # Antes de editar, la región es la de la cuenta. Después, manda la del
    # perfil: una cadena vacía significa «prefiero no indicarla» y no debe
    # volver a tomar el valor de la cuenta.
    region = (perfil.region or "") if perfil is not None else usuario.region
    return PerfilPublico(
        id_usuario=usuario.id_usuario,
        nombre=usuario.nombre,
        rol=usuario.rol,
        region=region,
        especialidad=perfil.especialidad if perfil else None,
        portafolio_url=perfil.portafolio_url if perfil else None,
        biografia=perfil.biografia if perfil else None,
    )


def actualizar(sesion: Session, usuario: Usuario, datos: PerfilEntrada) -> PerfilPublico:
    repo.guardar(
        sesion,
        id_usuario=usuario.id_usuario,
        especialidad=datos.especialidad,
        portafolio_url=datos.portafolio_url,
        biografia=datos.biografia,
        region=datos.region,
    )
    return ver(sesion, usuario.id_usuario)
