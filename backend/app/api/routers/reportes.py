"""Reportar contenido inapropiado (RF-38) o actualizaciones de eventos (RF-17). Requiere sesión."""
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, StringConstraints
from sqlalchemy import select

from app.core.deps import DbSession, Gestor, UsuarioActual
from app.models.enums import EstadoReporte, MotivoReporte, TipoObjetoReporte
from app.models.interaccion import Reporte
from app.patterns.observer import Eventos
from app.schemas.comun import Mensaje
from app.services.moderacion_service import MODELOS

router = APIRouter(prefix="/api/reportes", tags=["Moderación y seguridad"])


class ReporteIn(BaseModel):
    tipo_objeto: TipoObjetoReporte
    objeto_id: uuid.UUID
    motivo: MotivoReporte
    detalle: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] = ""


@router.post("", response_model=Mensaje, status_code=status.HTTP_201_CREATED, summary="Reportar contenido o un evento")
async def reportar(datos: ReporteIn, usuario: UsuarioActual, db: DbSession, gestor: Gestor, tareas: BackgroundTasks):
    if await db.get(MODELOS[datos.tipo_objeto], datos.objeto_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos lo que quieres reportar")
    if datos.motivo == MotivoReporte.ACTUALIZACION_EVENTO and datos.tipo_objeto != TipoObjetoReporte.EVENTO:
        raise HTTPException(422, "Ese motivo solo aplica a eventos")
    duplicado = await db.scalar(select(Reporte.id).where(
        Reporte.reportante_id == usuario.id, Reporte.objeto_id == datos.objeto_id,
        Reporte.estado == EstadoReporte.ABIERTO))
    if duplicado:
        return Mensaje(mensaje="Ya habías reportado esto. El equipo de moderación lo está revisando.")
    reporte = Reporte(reportante_id=usuario.id, **datos.model_dump())
    db.add(reporte)
    await db.commit()
    gestor.notificar_en_segundo_plano(
        tareas, Eventos.NUEVO_REPORTE,
        {"reporte_id": reporte.id, "tipo_objeto": datos.tipo_objeto, "motivo": datos.motivo},
        actor_id=usuario.id,
    )
    return Mensaje(mensaje="Gracias por avisar. El equipo de moderación revisará tu reporte.")
