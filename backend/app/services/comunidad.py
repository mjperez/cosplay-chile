"""Reglas de negocio del foro y de los desafíos mensuales."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.comunidad import DesafioMensual, ForoRespuesta, ForoTema
from app.models.usuario import Usuario
from app.repositories import comunidad as repo
from app.repositories import usuario as repo_usuarios
from app.schemas.comunidad import DesafioEntrada, RespuestaEntrada, TemaEntrada

__all__ = [
    "DesafioNoEncontrado",
    "MesDuplicado",
    "SinPermisos",
    "TemaCerrado",
    "TemaNoEncontrado",
    "UsuarioNoEncontrado",
    "cerrar_tema",
    "crear_desafio",
    "crear_tema",
    "desafio_vigente",
    "elegir_ganador",
    "listar_desafios",
    "listar_respuestas",
    "listar_temas",
    "obtener_tema",
    "responder",
]


class TemaNoEncontrado(Exception):
    pass


class TemaCerrado(Exception):
    """Un tema cerrado no admite respuestas nuevas."""


class SinPermisos(Exception):
    pass


class DesafioNoEncontrado(Exception):
    pass


class MesDuplicado(Exception):
    def __init__(self, mes: str) -> None:
        self.mes = mes
        super().__init__(f"ya existe un desafío para {mes}")


class UsuarioNoEncontrado(Exception):
    pass


# --- Foro ---------------------------------------------------------------

def listar_temas(
    sesion: Session,
    *,
    categoria: str | None = None,
    busqueda: str | None = None,
    limite: int = 20,
    desplazamiento: int = 0,
) -> tuple[int, list[tuple[ForoTema, str, int]]]:
    return repo.listar_temas(
        sesion,
        categoria=categoria,
        busqueda=busqueda,
        limite=limite,
        desplazamiento=desplazamiento,
    )


def obtener_tema(sesion: Session, id_tema: uuid.UUID) -> tuple[ForoTema, str, int]:
    fila = repo.obtener_tema(sesion, id_tema)
    if fila is None:
        raise TemaNoEncontrado(str(id_tema))
    return fila


def crear_tema(sesion: Session, datos: TemaEntrada, autor: Usuario) -> tuple[ForoTema, str, int]:
    tema = repo.crear_tema(
        sesion,
        id_creador=autor.id_usuario,
        titulo=datos.titulo.strip(),
        categoria=datos.categoria.strip(),
        contenido=datos.contenido.strip(),
    )
    return tema, autor.nombre, 0


def listar_respuestas(
    sesion: Session, id_tema: uuid.UUID
) -> list[tuple[ForoRespuesta, str]]:
    obtener_tema(sesion, id_tema)
    return repo.listar_respuestas(sesion, id_tema)


def responder(
    sesion: Session, id_tema: uuid.UUID, datos: RespuestaEntrada, autor: Usuario
) -> tuple[ForoRespuesta, str]:
    tema = obtener_tema(sesion, id_tema)[0]
    if tema.estado != "abierto":
        raise TemaCerrado(str(id_tema))
    respuesta = repo.crear_respuesta(
        sesion,
        id_tema=id_tema,
        id_usuario=autor.id_usuario,
        contenido=datos.contenido.strip(),
    )
    return respuesta, autor.nombre


def cerrar_tema(
    sesion: Session, id_tema: uuid.UUID, usuario: Usuario
) -> tuple[ForoTema, str, int]:
    tema, nombre, total = obtener_tema(sesion, id_tema)
    if tema.id_creador != usuario.id_usuario and usuario.rol != "administrador":
        raise SinPermisos(str(id_tema))
    repo.cambiar_estado(sesion, tema, "cerrado")
    return tema, nombre, total


# --- Desafíos -----------------------------------------------------------

def listar_desafios(sesion: Session) -> list[tuple[DesafioMensual, str | None]]:
    return repo.listar_desafios(sesion)


def desafio_vigente(sesion: Session) -> tuple[DesafioMensual, str | None] | None:
    mes = datetime.now(timezone.utc).strftime("%Y-%m")
    return repo.desafio_por_mes(sesion, mes)


def crear_desafio(sesion: Session, datos: DesafioEntrada) -> tuple[DesafioMensual, str | None]:
    if repo.desafio_por_mes(sesion, datos.mes) is not None:
        raise MesDuplicado(datos.mes)
    desafio = repo.crear_desafio(sesion, titulo=datos.titulo.strip(), mes=datos.mes)
    return desafio, None


def elegir_ganador(
    sesion: Session, id_desafio: uuid.UUID, id_usuario: uuid.UUID
) -> tuple[DesafioMensual, str | None]:
    fila = repo.obtener_desafio(sesion, id_desafio)
    if fila is None:
        raise DesafioNoEncontrado(str(id_desafio))
    usuario = repo_usuarios.obtener_por_id(sesion, id_usuario)
    if usuario is None:
        raise UsuarioNoEncontrado(str(id_usuario))
    repo.asignar_ganador(sesion, fila[0], id_usuario)
    return fila[0], usuario.nombre
