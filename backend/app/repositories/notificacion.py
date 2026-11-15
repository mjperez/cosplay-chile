"""Acceso a notificaciones y a la bitácora de auditoría."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notificacion import BitacoraAuditoria, Notificacion


def listar(
    sesion: Session,
    id_usuario: uuid.UUID,
    *,
    limite: int = 20,
    desplazamiento: int = 0,
    solo_no_leidas: bool = False,
) -> tuple[int, list[Notificacion]]:
    condiciones = [Notificacion.id_usuario == id_usuario]
    if solo_no_leidas:
        condiciones.append(Notificacion.leida.is_(False))
    total = sesion.scalar(
        select(func.count()).select_from(Notificacion).where(*condiciones)
    ) or 0
    filas = list(
        sesion.scalars(
            select(Notificacion)
            .where(*condiciones)
            .order_by(Notificacion.creado_en.desc())
            .limit(limite)
            .offset(desplazamiento)
        ).all()
    )
    return total, filas


def total_sin_leer(sesion: Session, id_usuario: uuid.UUID) -> int:
    return (
        sesion.scalar(
            select(func.count())
            .select_from(Notificacion)
            .where(
                Notificacion.id_usuario == id_usuario,
                Notificacion.leida.is_(False),
            )
        )
        or 0
    )


def obtener(
    sesion: Session, id_notificacion: uuid.UUID, id_usuario: uuid.UUID
) -> Notificacion | None:
    """Solo devuelve notificaciones del dueño: un 404 no revela ajenos."""
    return sesion.scalar(
        select(Notificacion).where(
            Notificacion.id_notificacion == id_notificacion,
            Notificacion.id_usuario == id_usuario,
        )
    )


def marcar_leida(sesion: Session, fila: Notificacion) -> Notificacion:
    fila.leida = True
    sesion.flush()
    return fila


def listar_auditoria(
    sesion: Session, *, limite: int = 50, desplazamiento: int = 0
) -> tuple[int, list[BitacoraAuditoria]]:
    total = sesion.scalar(
        select(func.count()).select_from(BitacoraAuditoria)
    ) or 0
    filas = list(
        sesion.scalars(
            select(BitacoraAuditoria)
            .order_by(BitacoraAuditoria.ocurrido_en.desc())
            .limit(limite)
            .offset(desplazamiento)
        ).all()
    )
    return total, filas
