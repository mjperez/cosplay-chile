"""Consultas del foro y de los desafíos mensuales."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.comunidad import DesafioMensual, ForoRespuesta, ForoTema
from app.models.usuario import Usuario

CATEGORIAS_FORO = (
    "Armaduras y props",
    "Pelucas y maquillaje",
    "Costura y vestuario",
    "Presupuesto y compras",
    "Eventos y comunidad",
)


def _conteo_respuestas():
    """Subconsulta correlacionada: evita un GROUP BY y funciona en SQLite y PG."""
    return (
        select(func.count())
        .select_from(ForoRespuesta)
        .where(ForoRespuesta.id_tema == ForoTema.id_tema)
        .correlate(ForoTema)
        .scalar_subquery()
    )


def _condiciones_temas(categoria: str | None, busqueda: str | None) -> list:
    condiciones = [ForoTema.estado != "oculto"]
    if categoria:
        condiciones.append(func.lower(ForoTema.categoria) == categoria.lower())
    if busqueda:
        patron = f"%{busqueda.strip()}%"
        condiciones.append(
            or_(ForoTema.titulo.ilike(patron), ForoTema.contenido.ilike(patron))
        )
    return condiciones


def _filtros(consulta: Select, condiciones: list) -> Select:
    for condicion in condiciones:
        consulta = consulta.where(condicion)
    return consulta


def listar_temas(
    sesion: Session,
    *,
    categoria: str | None = None,
    busqueda: str | None = None,
    limite: int = 20,
    desplazamiento: int = 0,
) -> tuple[int, list[tuple[ForoTema, str, int]]]:
    condiciones = _condiciones_temas(categoria, busqueda)

    total = sesion.scalar(
        _filtros(
            select(func.count()).select_from(ForoTema), condiciones
        )
    ) or 0

    filas = sesion.execute(
        _filtros(
            select(ForoTema, Usuario.nombre, _conteo_respuestas()).join(
                Usuario, Usuario.id_usuario == ForoTema.id_creador
            ),
            condiciones,
        )
        .order_by(ForoTema.creado_en.desc())
        .limit(limite)
        .offset(desplazamiento)
    ).all()
    return total, [(fila[0], fila[1], fila[2] or 0) for fila in filas]


def obtener_tema(sesion: Session, id_tema: uuid.UUID) -> tuple[ForoTema, str, int] | None:
    fila = sesion.execute(
        select(ForoTema, Usuario.nombre, _conteo_respuestas())
        .join(Usuario, Usuario.id_usuario == ForoTema.id_creador)
        .where(ForoTema.id_tema == id_tema, ForoTema.estado != "oculto")
    ).first()
    if fila is None:
        return None
    return fila[0], fila[1], fila[2] or 0


def crear_tema(
    sesion: Session,
    *,
    id_creador: uuid.UUID,
    titulo: str,
    categoria: str,
    contenido: str,
) -> ForoTema:
    tema = ForoTema(
        id_creador=id_creador,
        titulo=titulo,
        categoria=categoria,
        contenido=contenido,
        estado="abierto",
    )
    sesion.add(tema)
    sesion.flush()
    return tema


def tema_por_titulo(sesion: Session, titulo: str) -> ForoTema | None:
    """Idéntico a `evento.por_nombre`: `lower()` de SQLite no entiende tildes."""
    buscado = titulo.strip().lower()
    return next(
        (t for t in sesion.scalars(select(ForoTema)) if t.titulo.lower() == buscado),
        None,
    )


def cambiar_estado(sesion: Session, tema: ForoTema, estado: str) -> ForoTema:
    tema.estado = estado
    sesion.flush()
    return tema


def listar_respuestas(
    sesion: Session, id_tema: uuid.UUID
) -> list[tuple[ForoRespuesta, str]]:
    filas = sesion.execute(
        select(ForoRespuesta, Usuario.nombre)
        .join(Usuario, Usuario.id_usuario == ForoRespuesta.id_usuario)
        .where(ForoRespuesta.id_tema == id_tema)
        .order_by(ForoRespuesta.creado_en.asc(), ForoRespuesta.id_respuesta.asc())
    ).all()
    return [(fila[0], fila[1]) for fila in filas]


def crear_respuesta(
    sesion: Session,
    *,
    id_tema: uuid.UUID,
    id_usuario: uuid.UUID,
    contenido: str,
) -> ForoRespuesta:
    respuesta = ForoRespuesta(
        id_tema=id_tema, id_usuario=id_usuario, contenido=contenido
    )
    sesion.add(respuesta)
    sesion.flush()
    return respuesta


# --- Desafíos -----------------------------------------------------------

def _consulta_desafios():
    return select(DesafioMensual, Usuario.nombre).outerjoin(
        Usuario, Usuario.id_usuario == DesafioMensual.id_ganador
    )


def listar_desafios(sesion: Session) -> list[tuple[DesafioMensual, str | None]]:
    filas = sesion.execute(
        _consulta_desafios().order_by(DesafioMensual.mes.desc())
    ).all()
    return [(fila[0], fila[1]) for fila in filas]


def obtener_desafio(sesion: Session, id_desafio: uuid.UUID) -> tuple[DesafioMensual, str | None] | None:
    fila = sesion.execute(
        _consulta_desafios().where(DesafioMensual.id_desafio == id_desafio)
    ).first()
    return None if fila is None else (fila[0], fila[1])


def desafio_por_mes(sesion: Session, mes: str) -> tuple[DesafioMensual, str | None] | None:
    fila = sesion.execute(
        _consulta_desafios().where(DesafioMensual.mes == mes)
    ).first()
    return None if fila is None else (fila[0], fila[1])


def crear_desafio(sesion: Session, *, titulo: str, mes: str) -> DesafioMensual:
    desafio = DesafioMensual(titulo=titulo, mes=mes)
    sesion.add(desafio)
    sesion.flush()
    return desafio


def asignar_ganador(
    sesion: Session, desafio: DesafioMensual, id_usuario: uuid.UUID
) -> DesafioMensual:
    desafio.id_ganador = id_usuario
    sesion.flush()
    return desafio
