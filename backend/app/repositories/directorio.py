"""Consultas de «dónde comprar» y de grupos de la comunidad."""

from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.directorio import ComunidadGrupo, DondeComprar


def _filtros_tiendas(
    consulta: Select, *, tipo: str | None, region: str | None, busqueda: str | None
) -> Select:
    if tipo:
        consulta = consulta.where(DondeComprar.tipo == tipo)
    if region:
        consulta = consulta.where(func.lower(DondeComprar.region) == region.lower())
    if busqueda:
        patron = f"%{busqueda.strip()}%"
        consulta = consulta.where(DondeComprar.nombre.ilike(patron))
    return consulta


def listar_tiendas(
    sesion: Session,
    *,
    tipo: str | None = None,
    region: str | None = None,
    busqueda: str | None = None,
    limite: int = 50,
    desplazamiento: int = 0,
) -> tuple[int, list[DondeComprar]]:
    total = sesion.scalar(
        _filtros_tiendas(
            select(func.count()).select_from(DondeComprar),
            tipo=tipo,
            region=region,
            busqueda=busqueda,
        )
    ) or 0
    filas = sesion.scalars(
        _filtros_tiendas(
            select(DondeComprar), tipo=tipo, region=region, busqueda=busqueda
        )
        .order_by(DondeComprar.nombre.asc())
        .limit(limite)
        .offset(desplazamiento)
    )
    return total, list(filas)


def tienda_por_nombre(sesion: Session, nombre: str) -> DondeComprar | None:
    """Comparar en Python evita el `lower()` ASCII de SQLite con nombres con ñ."""
    buscado = nombre.strip().lower()
    return next(
        (t for t in sesion.scalars(select(DondeComprar)) if t.nombre.lower() == buscado),
        None,
    )


def crear_tienda(
    sesion: Session,
    *,
    nombre: str,
    tipo: str,
    envia_a_chile: bool,
    enlace_web: str | None,
    region: str | None,
) -> DondeComprar:
    tienda = DondeComprar(
        nombre=nombre,
        tipo=tipo,
        envia_a_chile=envia_a_chile,
        enlace_web=enlace_web,
        region=region,
    )
    sesion.add(tienda)
    sesion.flush()
    return tienda


def listar_grupos(
    sesion: Session,
    *,
    region: str | None = None,
    plataforma: str | None = None,
    limite: int = 50,
    desplazamiento: int = 0,
) -> tuple[int, list[ComunidadGrupo]]:
    consulta = select(ComunidadGrupo)
    if region:
        consulta = consulta.where(func.lower(ComunidadGrupo.region) == region.lower())
    if plataforma:
        consulta = consulta.where(ComunidadGrupo.plataforma == plataforma)

    total = sesion.scalar(
        select(func.count()).select_from(consulta.subquery())
    ) or 0
    filas = sesion.scalars(
        consulta.order_by(ComunidadGrupo.nombre.asc()).limit(limite).offset(desplazamiento)
    )
    return total, list(filas)


def grupo_por_nombre(sesion: Session, nombre: str) -> ComunidadGrupo | None:
    buscado = nombre.strip().lower()
    return next(
        (g for g in sesion.scalars(select(ComunidadGrupo)) if g.nombre.lower() == buscado),
        None,
    )


def crear_grupo(
    sesion: Session,
    *,
    nombre: str,
    region: str | None,
    plataforma: str,
    enlace: str | None,
) -> ComunidadGrupo:
    grupo = ComunidadGrupo(
        nombre=nombre, region=region, plataforma=plataforma, enlace=enlace
    )
    sesion.add(grupo)
    sesion.flush()
    return grupo
