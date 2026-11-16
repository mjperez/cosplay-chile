"""Calendario de eventos cosplay en Chile (RF-15, 16, 17)."""
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import delete, func, or_, select

from app.core.deps import DbSession, Gestor, UsuarioActual, UsuarioOpcional
from app.models.enums import REGION_CENTRO, EstadoPublicacion, Region, TipoEvento
from app.models.evento import Evento, ParticipacionEvento
from app.models.interaccion import Favorito
from app.patterns.observer import Eventos
from app.schemas.comun import Pagina
from app.schemas.evento import Asistencia, EventoDetalle, EventoOut, EventoSugerido
from app.services.busqueda_util import coincide

router = APIRouter(prefix="/api/eventos", tags=["Calendario de eventos"])


@router.get("", response_model=Pagina[EventoOut], summary="Eventos publicados (por defecto, desde hoy)")
async def listar(
    db: DbSession,
    region: Region | None = None,
    tipo: TipoEvento | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=100)] = 20,
):
    desde = desde or date.today()
    filtros = [
        Evento.estado == EstadoPublicacion.PUBLICADO,
        func.coalesce(Evento.fecha_fin, Evento.fecha_inicio) >= desde,  # incluye eventos en curso
    ]
    if hasta:
        filtros.append(Evento.fecha_inicio <= hasta)
    if region:
        filtros.append(Evento.region == region)
    if tipo:
        filtros.append(Evento.tipo == tipo)
    if q:
        filtros.append(or_(coincide(Evento.nombre, q), coincide(Evento.lugar, q), coincide(Evento.comuna, q)))
    total = await db.scalar(select(func.count()).select_from(Evento).where(*filtros))
    filas = (await db.execute(
        select(Evento).where(*filtros).order_by(Evento.fecha_inicio, Evento.nombre)
        .offset((pagina - 1) * por_pagina).limit(por_pagina)
    )).scalars().unique().all()
    return Pagina.crear([EventoOut.de(e) for e in filas], total or 0, pagina, por_pagina)


@router.post("/sugerir", response_model=EventoOut, status_code=status.HTTP_201_CREATED,
             summary="Sugerir un evento (RF-17): queda pendiente de revisión")
async def sugerir(datos: EventoSugerido, usuario: UsuarioActual, db: DbSession, gestor: Gestor, tareas: BackgroundTasks):
    lat, lng = REGION_CENTRO[datos.region]
    evento = Evento(**datos.model_dump(), lat=lat, lng=lng, estado=EstadoPublicacion.PENDIENTE, creado_por_id=usuario.id)
    evento.creado_por = usuario
    db.add(evento)
    await db.commit()
    gestor.notificar_en_segundo_plano(
        tareas, Eventos.EVENTO_SUGERIDO, {"evento_id": evento.id, "nombre": evento.nombre, "autor_id": usuario.id},
        actor_id=usuario.id,
    )
    return EventoOut.de(evento)


async def _visible(db, evento_id: uuid.UUID, usuario) -> Evento:
    e = await db.get(Evento, evento_id)
    if e is None or (e.estado != EstadoPublicacion.PUBLICADO and not (
            usuario and (usuario.es_admin or usuario.id == e.creado_por_id))):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")
    return e


async def _asistentes(db, evento_id) -> int:
    return await db.scalar(select(func.count()).select_from(ParticipacionEvento).where(
        ParticipacionEvento.evento_id == evento_id)) or 0


@router.get("/{evento_id}", response_model=EventoDetalle, summary="Detalle de un evento")
async def detalle(evento_id: uuid.UUID, db: DbSession, usuario: UsuarioOpcional):
    e = await _visible(db, evento_id, usuario)
    fav = asistire = False
    if usuario:
        fav = await db.scalar(select(Favorito.id).where(Favorito.usuario_id == usuario.id, Favorito.evento_id == e.id)) is not None
        asistire = await db.scalar(select(ParticipacionEvento.id).where(
            ParticipacionEvento.usuario_id == usuario.id, ParticipacionEvento.evento_id == e.id)) is not None
    return EventoDetalle(**EventoOut.de(e).model_dump(), es_favorito=fav, asistire=asistire,
                         asistentes=await _asistentes(db, e.id))


@router.post("/{evento_id}/asistir", response_model=Asistencia, summary="Marcar o desmarcar «Asistiré»")
async def asistir(evento_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    e = await _visible(db, evento_id, usuario)
    if e.estado != EstadoPublicacion.PUBLICADO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El evento aún no está publicado")
    existente = await db.scalar(select(ParticipacionEvento).where(
        ParticipacionEvento.usuario_id == usuario.id, ParticipacionEvento.evento_id == e.id))
    if existente:
        await db.execute(delete(ParticipacionEvento).where(ParticipacionEvento.id == existente.id))
    else:
        db.add(ParticipacionEvento(usuario_id=usuario.id, evento_id=e.id, rol="asistente"))
    await db.commit()
    return Asistencia(asistire=existente is None, asistentes=await _asistentes(db, e.id))


@router.get("/sugeridos/mios", response_model=list[EventoOut], summary="Eventos que sugerí")
async def mis_sugerencias(usuario: UsuarioActual, db: DbSession):
    filas = (await db.execute(
        select(Evento).where(Evento.creado_por_id == usuario.id).order_by(Evento.created_at.desc())
    )).scalars().unique().all()
    return [EventoOut.de(e) for e in filas]

