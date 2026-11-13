"""Consultas del contenido editorial."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.contenido import CategoriaContenido, Contenido


def _filtrar(
    consulta: Select, *, estado: str | None, tipo: str | None
) -> Select:
    if estado:
        consulta = consulta.where(Contenido.estado == estado)
    if tipo:
        consulta = consulta.where(Contenido.tipo == tipo)
    return consulta


def listar(
    sesion: Session,
    *,
    estado: str | None = None,
    tipo: str | None = None,
    limite: int = 20,
    desplazamiento: int = 0,
) -> tuple[int, list[Contenido]]:
    total = sesion.scalar(
        _filtrar(select(func.count()).select_from(Contenido), estado=estado, tipo=tipo)
    ) or 0

    pagina = sesion.scalars(
        _filtrar(select(Contenido), estado=estado, tipo=tipo)
        .order_by(Contenido.creado_en.desc())
        .limit(limite)
        .offset(desplazamiento)
    )
    return total, list(pagina)


def obtener(sesion: Session, id_contenido: uuid.UUID) -> Contenido | None:
    return sesion.get(Contenido, id_contenido)


def por_titulo(sesion: Session, titulo: str) -> Contenido | None:
    """Búsqueda exacta por título, usada por la semilla de demostración."""
    return sesion.scalar(select(Contenido).where(Contenido.titulo == titulo))


def listar_categorias(sesion: Session) -> list[CategoriaContenido]:
    return list(sesion.scalars(select(CategoriaContenido).order_by(CategoriaContenido.nombre)))


def categoria_por_nombre(sesion: Session, nombre: str) -> CategoriaContenido | None:
    return sesion.scalar(
        select(CategoriaContenido).where(func.lower(CategoriaContenido.nombre) == nombre.lower())
    )


def crear_categoria(
    sesion: Session, *, nombre: str, descripcion: str | None
) -> CategoriaContenido:
    categoria = CategoriaContenido(nombre=nombre, descripcion=descripcion)
    sesion.add(categoria)
    sesion.flush()
    return categoria
