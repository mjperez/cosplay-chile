"""Perfil público de cosplayer."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.perfil import PerfilEntrada, PerfilPublico
from app.services import perfil as servicio

router = APIRouter(prefix="/perfiles", tags=["perfiles"])


@router.get("/mio", response_model=PerfilPublico, summary="Ver mi perfil")
def mi_perfil(usuario: Usuario = Depends(get_usuario_actual), sesion: Session = Depends(get_db)) -> PerfilPublico:
    return servicio.ver(sesion, usuario.id_usuario)


@router.put("/mio", response_model=PerfilPublico, summary="Actualizar mi perfil")
def actualizar_mi_perfil(
    datos: PerfilEntrada,
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> PerfilPublico:
    return servicio.actualizar(sesion, usuario, datos)


@router.get("/{id_usuario}", response_model=PerfilPublico, summary="Ver el perfil de un usuario")
def ver_perfil(id_usuario: uuid.UUID, sesion: Session = Depends(get_db)) -> PerfilPublico:
    try:
        return servicio.ver(sesion, id_usuario)
    except servicio.UsuarioNoEncontrado:
        raise HTTPException(404, "usuario no encontrado")
