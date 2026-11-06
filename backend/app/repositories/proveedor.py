"""Consultas del directorio de proveedores."""

from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.directorio import Proveedor


def _aplicar_filtros(
    consulta: Select,
    *,
    region: str | None,
    tipo: str | None,
    busqueda: str | None,
    sin_region: bool,
) -> Select:
    if region:
        consulta = consulta.where(func.lower(Proveedor.region) == region.lower())
    if sin_region:
        consulta = consulta.where(Proveedor.region.is_(None))
    if tipo:
        consulta = consulta.where(Proveedor.tipo == tipo)
    if busqueda:
        patron = f"%{busqueda.strip()}%"
        consulta = consulta.where(
            or_(
                Proveedor.nombre.ilike(patron),
                Proveedor.descripcion.ilike(patron),
            )
        )
    return consulta


def listar(
    sesion: Session,
    *,
    region: str | None = None,
    tipo: str | None = None,
    busqueda: str | None = None,
    sin_region: bool = False,
    limite: int = 20,
    desplazamiento: int = 0,
) -> tuple[int, list[Proveedor]]:
    """Devuelve el total que cumple los filtros y la página pedida."""
    base = select(Proveedor).where(Proveedor.activo.is_(True))
    base = _aplicar_filtros(
        base, region=region, tipo=tipo, busqueda=busqueda, sin_region=sin_region
    )

    total = sesion.scalar(
        _aplicar_filtros(
            select(func.count()).select_from(Proveedor).where(Proveedor.activo.is_(True)),
            region=region,
            tipo=tipo,
            busqueda=busqueda,
            sin_region=sin_region,
        )
    ) or 0

    pagina = sesion.scalars(
        base.order_by(Proveedor.nombre.asc()).limit(limite).offset(desplazamiento)
    )
    return total, list(pagina)


def regiones_disponibles(sesion: Session) -> list[str]:
    """Regiones que efectivamente tienen fichas, en orden alfabético."""
    consulta = (
        select(Proveedor.region)
        .where(Proveedor.activo.is_(True), Proveedor.region.is_not(None))
        .distinct()
        .order_by(Proveedor.region.asc())
    )
    return [r for r in sesion.scalars(consulta) if r]


def tipos_disponibles(sesion: Session) -> list[str]:
    consulta = (
        select(Proveedor.tipo)
        .where(Proveedor.activo.is_(True))
        .distinct()
        .order_by(Proveedor.tipo.asc())
    )
    return list(sesion.scalars(consulta))
