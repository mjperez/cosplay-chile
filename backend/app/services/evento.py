"""Reglas de negocio del calendario de eventos."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.evento import EventoCosplay, ParticipacionEvento
from app.models.usuario import Usuario
from app.repositories import evento as repo
from app.schemas.evento import EventoEntrada

__all__ = [
    "EventoNoEncontrado",
    "ParticipacionDuplicada",
    "ParticipacionInexistente",
    "cancelar",
    "crear",
    "inscribirse",
    "listar",
    "mis_eventos",
    "obtener",
    "participaciones",
]


class EventoNoEncontrado(Exception):
    pass


class ParticipacionDuplicada(Exception):
    """La restricción de unicidad es por (usuario, evento), no por personaje."""


class ParticipacionInexistente(Exception):
    pass


def listar(
    sesion: Session,
    *,
    tipo: str | None = None,
    region: str | None = None,
    busqueda: str | None = None,
    limite: int = 20,
    desplazamiento: int = 0,
) -> tuple[int, list[EventoCosplay]]:
    return repo.listar(
        sesion,
        tipo=tipo,
        region=region,
        busqueda=busqueda,
        limite=limite,
        desplazamiento=desplazamiento,
    )


def obtener(sesion: Session, id_evento: uuid.UUID) -> EventoCosplay:
    evento = repo.obtener(sesion, id_evento)
    if evento is None:
        raise EventoNoEncontrado(str(id_evento))
    return evento


def crear(sesion: Session, datos: EventoEntrada) -> EventoCosplay:
    return repo.crear(
        sesion,
        nombre=datos.nombre.strip(),
        tipo=datos.tipo,
        fecha_inicio=datos.fecha_inicio,
        fecha_fin=datos.fecha_fin,
        lugar=datos.lugar.strip(),
        region=datos.region,
        enlace_oficial=datos.enlace_oficial,
    )


def inscribirse(
    sesion: Session,
    id_evento: uuid.UUID,
    usuario: Usuario,
    personaje: str | None,
) -> ParticipacionEvento:
    obtener(sesion, id_evento)  # 404 antes que 409: no se revela nada de un evento ajeno
    if repo.participacion(sesion, usuario.id_usuario, id_evento) is not None:
        raise ParticipacionDuplicada(str(id_evento))
    return repo.crear_participacion(
        sesion,
        id_usuario=usuario.id_usuario,
        id_evento=id_evento,
        personaje=personaje.strip() if personaje else None,
    )


def cancelar(sesion: Session, id_evento: uuid.UUID, usuario: Usuario) -> None:
    obtener(sesion, id_evento)
    fila = repo.participacion(sesion, usuario.id_usuario, id_evento)
    if fila is None:
        raise ParticipacionInexistente(str(id_evento))
    repo.eliminar_participacion(sesion, fila)


def participaciones(
    sesion: Session, id_evento: uuid.UUID
) -> list[tuple[ParticipacionEvento, str]]:
    obtener(sesion, id_evento)
    return repo.listar_participaciones(sesion, id_evento)


def mis_eventos(sesion: Session, id_usuario: uuid.UUID) -> list[EventoCosplay]:
    return repo.listar_inscripciones(sesion, id_usuario)
