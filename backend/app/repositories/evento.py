"""Consultas de eventos y de participaciones."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.evento import EventoCosplay, ParticipacionEvento
from app.models.usuario import Usuario

TIPOS_EVENTO = ("convencion", "concurso", "feria", "taller", "otro")


def _filtros(consulta: Select, *, tipo: str | None, region: str | None, busqueda: str | None) -> Select:
    if tipo:
        consulta = consulta.where(EventoCosplay.tipo == tipo)
    if region:
        consulta = consulta.where(func.lower(EventoCosplay.region) == region.lower())
    if busqueda:
        patron = f"%{busqueda.strip()}%"
        consulta = consulta.where(
            or_(
                EventoCosplay.nombre.ilike(patron),
                EventoCosplay.lugar.ilike(patron),
            )
        )
    return consulta


def listar(
    sesion: Session,
    *,
    tipo: str | None = None,
    region: str | None = None,
    busqueda: str | None = None,
    limite: int = 20,
    desplazamiento: int = 0,
) -> tuple[int, list[EventoCosplay]]:
    total = sesion.scalar(
        _filtros(
            select(func.count()).select_from(EventoCosplay),
            tipo=tipo,
            region=region,
            busqueda=busqueda,
        )
    ) or 0

    filas = sesion.scalars(
        _filtros(select(EventoCosplay), tipo=tipo, region=region, busqueda=busqueda)
        .order_by(EventoCosplay.fecha_inicio.asc())
        .limit(limite)
        .offset(desplazamiento)
    )
    return total, list(filas)


def obtener(sesion: Session, id_evento: uuid.UUID) -> EventoCosplay | None:
    return sesion.get(EventoCosplay, id_evento)


def por_nombre(sesion: Session, nombre: str) -> EventoCosplay | None:
    """Comparación sin distinguir mayúsculas hecha en Python.

    `lower()` de SQLite solo entiende ASCII: con nombres como «Ñuñoa» dejaría
    la Ñ intacta y la semilla crearía un duplicado en cada ejecución.
    """
    buscado = nombre.strip().lower()
    return next(
        (e for e in sesion.scalars(select(EventoCosplay)) if e.nombre.lower() == buscado),
        None,
    )


def crear(
    sesion: Session,
    *,
    nombre: str,
    tipo: str,
    fecha_inicio: datetime,
    fecha_fin: datetime | None,
    lugar: str,
    region: str | None,
    enlace_oficial: str | None,
) -> EventoCosplay:
    evento = EventoCosplay(
        nombre=nombre,
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        lugar=lugar,
        region=region,
        enlace_oficial=enlace_oficial,
    )
    sesion.add(evento)
    sesion.flush()
    return evento


def contar_participaciones(sesion: Session, id_evento: uuid.UUID) -> int:
    return sesion.scalar(
        select(func.count())
        .select_from(ParticipacionEvento)
        .where(ParticipacionEvento.id_evento == id_evento)
    ) or 0


def participacion(
    sesion: Session, id_usuario: uuid.UUID, id_evento: uuid.UUID
) -> ParticipacionEvento | None:
    return sesion.scalar(
        select(ParticipacionEvento).where(
            ParticipacionEvento.id_usuario == id_usuario,
            ParticipacionEvento.id_evento == id_evento,
        )
    )


def crear_participacion(
    sesion: Session,
    *,
    id_usuario: uuid.UUID,
    id_evento: uuid.UUID,
    personaje: str | None,
) -> ParticipacionEvento:
    fila = ParticipacionEvento(
        id_usuario=id_usuario, id_evento=id_evento, personaje=personaje
    )
    sesion.add(fila)
    sesion.flush()
    return fila


def eliminar_participacion(sesion: Session, fila: ParticipacionEvento) -> None:
    sesion.delete(fila)
    sesion.flush()


def listar_participaciones(
    sesion: Session, id_evento: uuid.UUID
) -> list[tuple[ParticipacionEvento, str]]:
    filas = sesion.execute(
        select(ParticipacionEvento, Usuario.nombre)
        .join(Usuario, Usuario.id_usuario == ParticipacionEvento.id_usuario)
        .where(ParticipacionEvento.id_evento == id_evento)
        .order_by(ParticipacionEvento.id_participacion)
    ).all()
    return [(fila[0], fila[1]) for fila in filas]


def listar_inscripciones(sesion: Session, id_usuario: uuid.UUID) -> list[EventoCosplay]:
    return list(
        sesion.scalars(
            select(EventoCosplay)
            .join(ParticipacionEvento, ParticipacionEvento.id_evento == EventoCosplay.id_evento)
            .where(ParticipacionEvento.id_usuario == id_usuario)
            .order_by(EventoCosplay.fecha_inicio.asc())
        )
    )
