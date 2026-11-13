"""Reglas de negocio del panel de administración.

Cada operación valida antes de escribir y lanza una excepción de dominio; el
router traduce esas excepciones a 404/409/403. Así las reglas siguen siendo
testeables sin levantar HTTP, igual que en los demás módulos.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.comunidad import ForoTema
from app.models.contenido import Contenido
from app.models.directorio import ComunidadGrupo, DondeComprar
from app.models.evento import EventoCosplay
from app.models.usuario import Usuario
from app.repositories import admin as repo
from app.repositories import directorio as repo_directorio
from app.repositories import usuario as repo_usuarios
from app.schemas.admin import GrupoEntrada, ResumenAdmin, TiendaEntrada

__all__ = [
    "AutoBloqueo",
    "ContenidoNoEncontrado",
    "EventoNoEncontrado",
    "NombreDuplicado",
    "TemaNoEncontrado",
    "TransicionInvalida",
    "UsuarioNoEncontrado",
    "cambiar_estado_contenido",
    "cambiar_estado_tema",
    "cambiar_estado_usuario",
    "crear_grupo",
    "crear_tienda",
    "eliminar_evento",
    "resumen",
]

# Transiciones permitidas en la bandeja editorial. Un contenido publicado no
# se «rechaza» directamente: primero vuelve a borrador, para que quede claro
# que se está retirando una publicación y no editando un borrador.
TRANSICIONES = {
    "pendiente": {"publicado", "rechazado"},
    "publicado": {"pendiente"},
    "rechazado": {"pendiente", "publicado"},
}


class UsuarioNoEncontrado(Exception):
    pass


class AutoBloqueo(Exception):
    """Un administrador no puede desactivarse a sí mismo y dejar el sistema sin acceso."""


class ContenidoNoEncontrado(Exception):
    pass


class TransicionInvalida(Exception):
    def __init__(self, origen: str, destino: str) -> None:
        self.origen = origen
        self.destino = destino
        super().__init__(f"no se puede pasar de «{origen}» a «{destino}»")


class EventoNoEncontrado(Exception):
    pass


class TemaNoEncontrado(Exception):
    pass


class NombreDuplicado(Exception):
    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        super().__init__(f"ya existe una entrada llamada «{nombre}»")


def resumen(sesion: Session) -> ResumenAdmin:
    return ResumenAdmin(**repo.resumen(sesion))


def cambiar_estado_usuario(
    sesion: Session,
    id_usuario: uuid.UUID,
    activo: bool,
    administrador: Usuario,
) -> Usuario:
    usuario = repo_usuarios.obtener_por_id(sesion, id_usuario)
    if usuario is None:
        raise UsuarioNoEncontrado(str(id_usuario))
    if usuario.id_usuario == administrador.id_usuario and not activo:
        raise AutoBloqueo()
    usuario.activo = activo
    sesion.flush()
    return usuario


def cambiar_estado_contenido(
    sesion: Session, id_contenido: uuid.UUID, destino: str
) -> Contenido:
    contenido = repo.obtener_contenido(sesion, id_contenido)
    if contenido is None:
        raise ContenidoNoEncontrado(str(id_contenido))
    if contenido.estado == destino:
        return contenido
    if destino not in TRANSICIONES.get(contenido.estado, set()):
        raise TransicionInvalida(contenido.estado, destino)

    contenido.estado = destino
    contenido.fecha_publicacion = (
        datetime.now(timezone.utc).replace(tzinfo=None) if destino == "publicado" else None
    )
    sesion.flush()
    return contenido


def eliminar_evento(sesion: Session, id_evento: uuid.UUID) -> None:
    evento: EventoCosplay | None = repo.obtener_evento(sesion, id_evento)
    if evento is None:
        raise EventoNoEncontrado(str(id_evento))
    repo.eliminar_evento(sesion, evento)


def cambiar_estado_tema(
    sesion: Session, id_tema: uuid.UUID, estado: str
) -> tuple[ForoTema, str, int]:
    fila = repo.obtener_tema(sesion, id_tema)
    if fila is None:
        raise TemaNoEncontrado(str(id_tema))
    tema, nombre, total = fila
    tema.estado = estado
    sesion.flush()
    return tema, nombre, total


def crear_tienda(sesion: Session, datos: TiendaEntrada) -> DondeComprar:
    if repo_directorio.tienda_por_nombre(sesion, datos.nombre) is not None:
        raise NombreDuplicado(datos.nombre)
    return repo_directorio.crear_tienda(
        sesion,
        nombre=datos.nombre,
        tipo=datos.tipo,
        envia_a_chile=datos.envia_a_chile,
        enlace_web=datos.enlace_web,
        region=datos.region,
    )


def crear_grupo(sesion: Session, datos: GrupoEntrada) -> ComunidadGrupo:
    if repo_directorio.grupo_por_nombre(sesion, datos.nombre) is not None:
        raise NombreDuplicado(datos.nombre)
    return repo_directorio.crear_grupo(
        sesion,
        nombre=datos.nombre,
        region=datos.region,
        plataforma=datos.plataforma,
        enlace=datos.enlace,
    )
