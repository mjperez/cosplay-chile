"""Notificaciones internas del usuario autenticado (RF-37).

El router completo exige sesión: no hay forma de leer los avisos de otra
cuenta, y `obtener()` además filtra por dueño para que un UUID ajeno devuelva
404 en vez de confirmar su existencia.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual
from app.core.database import get_db
from app.models.usuario import Usuario
from app.repositories import notificacion as repo
from app.schemas.notificacion import (
    NotificacionPublica,
    PaginaNotificaciones,
    ResumenNotificaciones,
)

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])


@router.get(
    "/sin-leer",
    response_model=ResumenNotificaciones,
    summary="Cantidad de notificaciones sin leer",
)
def resumen_notificaciones(
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> ResumenNotificaciones:
    return ResumenNotificaciones(sin_leer=repo.total_sin_leer(sesion, usuario.id_usuario))


@router.get(
    "", response_model=PaginaNotificaciones, summary="Mis notificaciones"
)
def listar_notificaciones(
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    solo_no_leidas: bool = Query(False, description="Solo avisos pendientes de lectura"),
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> PaginaNotificaciones:
    total, filas = repo.listar(
        sesion,
        usuario.id_usuario,
        limite=limite,
        desplazamiento=desplazamiento,
        solo_no_leidas=solo_no_leidas,
    )
    return PaginaNotificaciones(
        total=total,
        sin_leer=repo.total_sin_leer(sesion, usuario.id_usuario),
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[NotificacionPublica.model_validate(fila) for fila in filas],
    )


@router.patch(
    "/{id_notificacion}/leer",
    response_model=NotificacionPublica,
    summary="Marcar una notificación como leída",
)
def marcar_leida(
    id_notificacion: uuid.UUID,
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> NotificacionPublica:
    fila = repo.obtener(sesion, id_notificacion, usuario.id_usuario)
    if fila is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="notificación no encontrada"
        )
    return NotificacionPublica.model_validate(repo.marcar_leida(sesion, fila))
