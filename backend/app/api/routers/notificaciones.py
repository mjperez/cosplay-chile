"""Notificaciones internas (RF-37), generadas por NotificacionInternaObserver."""
import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select, update

from app.core.deps import DbSession, UsuarioActual
from app.models.interaccion import Notificacion
from app.schemas.comun import Mensaje, ModeloOrm

router = APIRouter(prefix="/api/notificaciones", tags=["Notificaciones"])


class NotificacionOut(ModeloOrm):
    id: uuid.UUID
    tipo: str
    mensaje: str
    enlace: str | None
    leida: bool
    created_at: datetime


class Bandeja(BaseModel):
    no_leidas: int
    items: list[NotificacionOut]


@router.get("", response_model=Bandeja, summary="Mis notificaciones recientes")
async def listar(usuario: UsuarioActual, db: DbSession, limite: int = 30):
    limite = max(1, min(limite, 100))
    items = (await db.execute(
        select(Notificacion).where(Notificacion.usuario_id == usuario.id)
        .order_by(Notificacion.created_at.desc()).limit(limite)
    )).scalars().all()
    no_leidas = await db.scalar(select(func.count()).select_from(Notificacion).where(
        Notificacion.usuario_id == usuario.id, Notificacion.leida.is_(False)))
    return Bandeja(no_leidas=no_leidas or 0, items=items)


@router.post("/leer-todas", response_model=Mensaje, summary="Marcar todas como leídas")
async def leer_todas(usuario: UsuarioActual, db: DbSession):
    await db.execute(update(Notificacion).where(Notificacion.usuario_id == usuario.id).values(leida=True))
    await db.commit()
    return Mensaje(mensaje="Notificaciones marcadas como leídas")


@router.post("/{notificacion_id}/leer", response_model=Mensaje, summary="Marcar una notificación como leída")
async def leer(notificacion_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    await db.execute(update(Notificacion).where(
        Notificacion.id == notificacion_id, Notificacion.usuario_id == usuario.id).values(leida=True))
    await db.commit()
    return Mensaje(mensaje="Notificación leída")
