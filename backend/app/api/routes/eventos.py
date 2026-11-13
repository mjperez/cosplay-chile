"""Calendario de eventos y participación de la comunidad."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual, requiere_admin
from app.core.database import get_db
from app.models.evento import EventoCosplay
from app.models.usuario import Usuario
from app.repositories import evento as repo
from app.schemas.evento import (
    EventoEntrada,
    EventoPublico,
    ListaEventos,
    PaginaEventos,
    PaginaParticipaciones,
    ParticipacionEntrada,
    ParticipacionPublica,
)
from app.services import evento as servicio

router = APIRouter(prefix="/eventos", tags=["eventos"])


def _publico(sesion: Session, evento: EventoCosplay) -> EventoPublico:
    return EventoPublico(
        id_evento=evento.id_evento,
        nombre=evento.nombre,
        tipo=evento.tipo,
        fecha_inicio=evento.fecha_inicio,
        fecha_fin=evento.fecha_fin,
        lugar=evento.lugar,
        region=evento.region,
        enlace_oficial=evento.enlace_oficial,
        total_participantes=repo.contar_participaciones(sesion, evento.id_evento),
        creado_en=evento.creado_en,
    )


@router.get("", response_model=PaginaEventos, summary="Listar eventos con filtros")
def listar_eventos(
    tipo: str | None = Query(None, description=f"Uno de: {', '.join(repo.TIPOS_EVENTO)}"),
    region: str | None = Query(None, description="Región exacta, sin distinguir mayúsculas"),
    q: str | None = Query(None, max_length=80, description="Texto sobre nombre o lugar"),
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
) -> PaginaEventos:
    total, elementos = servicio.listar(
        sesion,
        tipo=tipo,
        region=region,
        busqueda=q,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return PaginaEventos(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[_publico(sesion, e) for e in elementos],
    )


@router.get("/mis", response_model=ListaEventos, summary="Eventos en los que estoy inscrito")
def mis_eventos(
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> ListaEventos:
    elementos = servicio.mis_eventos(sesion, usuario.id_usuario)
    return ListaEventos(
        total=len(elementos),
        elementos=[_publico(sesion, e) for e in elementos],
    )


@router.get("/{id_evento}", response_model=EventoPublico, summary="Detalle de un evento")
def detalle_evento(id_evento: uuid.UUID, sesion: Session = Depends(get_db)) -> EventoPublico:
    try:
        evento = servicio.obtener(sesion, id_evento)
    except servicio.EventoNoEncontrado:
        raise HTTPException(404, "evento no encontrado")
    return _publico(sesion, evento)


@router.get(
    "/{id_evento}/participaciones",
    response_model=PaginaParticipaciones,
    summary="Participantes inscritos en un evento",
)
def participaciones_evento(
    id_evento: uuid.UUID, sesion: Session = Depends(get_db)
) -> PaginaParticipaciones:
    try:
        filas = servicio.participaciones(sesion, id_evento)
    except servicio.EventoNoEncontrado:
        raise HTTPException(404, "evento no encontrado")
    return PaginaParticipaciones(
        total=len(filas),
        elementos=[
            ParticipacionPublica(
                id_participacion=fila.id_participacion,
                id_usuario=fila.id_usuario,
                id_evento=fila.id_evento,
                personaje=fila.personaje,
                nombre_usuario=nombre,
            )
            for fila, nombre in filas
        ],
    )


@router.post(
    "",
    response_model=EventoPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un evento (solo administrador)",
    dependencies=[Depends(requiere_admin)],
)
def crear_evento(datos: EventoEntrada, sesion: Session = Depends(get_db)) -> EventoPublico:
    evento = servicio.crear(sesion, datos)
    return _publico(sesion, evento)


@router.post(
    "/{id_evento}/participar",
    response_model=ParticipacionPublica,
    status_code=status.HTTP_201_CREATED,
    summary="Inscribirse en un evento",
)
def participar(
    id_evento: uuid.UUID,
    datos: ParticipacionEntrada,
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> ParticipacionPublica:
    try:
        fila = servicio.inscribirse(sesion, id_evento, usuario, datos.personaje)
    except servicio.EventoNoEncontrado:
        raise HTTPException(404, "evento no encontrado")
    except servicio.ParticipacionDuplicada:
        raise HTTPException(409, "ya estás inscrito en este evento")
    return ParticipacionPublica(
        id_participacion=fila.id_participacion,
        id_usuario=fila.id_usuario,
        id_evento=fila.id_evento,
        personaje=fila.personaje,
        nombre_usuario=usuario.nombre,
    )


@router.delete(
    "/{id_evento}/participar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancelar la inscripción en un evento",
)
def cancelar_participacion(
    id_evento: uuid.UUID,
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> Response:
    try:
        servicio.cancelar(sesion, id_evento, usuario)
    except servicio.EventoNoEncontrado:
        raise HTTPException(404, "evento no encontrado")
    except servicio.ParticipacionInexistente:
        raise HTTPException(404, "no tienes inscripción en este evento")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
