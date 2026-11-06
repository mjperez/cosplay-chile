"""Reglas de negocio del contenido editorial (US-08)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.factories.contenido_factory import ContenidoFactory, TipoContenidoInvalido
from app.models.contenido import CategoriaContenido, Contenido
from app.models.usuario import Usuario
from app.repositories import contenido as repo
from app.schemas.contenido import ContenidoEntrada

__all__ = [
    "CategoriaInexistente",
    "ContenidoNoEncontrado",
    "PublicacionInvalida",
    "TipoContenidoInvalido",
    "crear",
    "crear_categoria",
    "listar_publicos",
    "obtener_publico",
    "publicar",
]


class CategoriaInexistente(Exception):
    """La categoría indicada no está registrada."""

    def __init__(self, id_categoria: uuid.UUID) -> None:
        self.id_categoria = id_categoria
        super().__init__(f"no existe la categoría {id_categoria}")


class CategoriaDuplicada(Exception):
    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        super().__init__(f"la categoría «{nombre}» ya existe")


class ContenidoNoEncontrado(Exception):
    pass


class PublicacionInvalida(Exception):
    """Se intentó publicar algo que no está en borrador."""

    def __init__(self, estado: str) -> None:
        self.estado = estado
        super().__init__(f"no se puede publicar un contenido en estado «{estado}»")


def _validar_categoria(sesion: Session, id_categoria: uuid.UUID | None) -> None:
    if id_categoria is None:
        return
    if sesion.get(CategoriaContenido, id_categoria) is None:
        raise CategoriaInexistente(id_categoria)


def crear(sesion: Session, datos: ContenidoEntrada, autor: Usuario) -> Contenido:
    """Crea el contenido en estado borrador usando el Factory Method."""
    _validar_categoria(sesion, datos.id_categoria)

    contenido = ContenidoFactory.crear(datos, autor.id_usuario)
    sesion.add(contenido)
    sesion.flush()
    return contenido


def publicar(sesion: Session, id_contenido: uuid.UUID) -> Contenido:
    contenido = repo.obtener(sesion, id_contenido)
    if contenido is None:
        raise ContenidoNoEncontrado(str(id_contenido))
    if contenido.estado == "publicado":
        return contenido
    if contenido.estado != "pendiente":
        raise PublicacionInvalida(contenido.estado)

    contenido.estado = "publicado"
    contenido.fecha_publicacion = datetime.now(timezone.utc)
    sesion.flush()
    return contenido


def listar_publicos(
    sesion: Session,
    *,
    tipo: str | None = None,
    limite: int = 20,
    desplazamiento: int = 0,
) -> tuple[int, list[Contenido]]:
    return repo.listar(
        sesion, estado="publicado", tipo=tipo, limite=limite, desplazamiento=desplazamiento
    )


def obtener_publico(sesion: Session, id_contenido: uuid.UUID) -> Contenido:
    contenido = repo.obtener(sesion, id_contenido)
    # Un borrador responde 404, no 403: si respondiera 403 confirmaría que el
    # recurso existe, que es justo lo que no se quiere revelar.
    if contenido is None or contenido.estado != "publicado":
        raise ContenidoNoEncontrado(str(id_contenido))
    return contenido


def crear_categoria(sesion: Session, *, nombre: str, descripcion: str | None) -> CategoriaContenido:
    if repo.categoria_por_nombre(sesion, nombre) is not None:
        raise CategoriaDuplicada(nombre)
    return repo.crear_categoria(sesion, nombre=nombre.strip(), descripcion=descripcion)
