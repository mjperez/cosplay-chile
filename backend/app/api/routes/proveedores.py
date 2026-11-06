"""Directorio público de proveedores (US-13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.directorio import TIPOS_PROVEEDOR
from app.repositories import proveedor as repo
from app.schemas.proveedor import PaginaProveedores, ProveedorPublico

router = APIRouter(prefix="/proveedores", tags=["directorio"])


@router.get(
    "",
    response_model=PaginaProveedores,
    summary="Listar proveedores con filtros y paginación",
)
def listar_proveedores(
    region: str | None = Query(None, description="Región exacta, sin distinguir mayúsculas"),
    tipo: str | None = Query(None, description=f"Uno de: {', '.join(TIPOS_PROVEEDOR)}"),
    q: str | None = Query(None, max_length=80, description="Texto libre sobre nombre o descripción"),
    sin_region: bool = Query(False, description="Solo fichas que no declaran región"),
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
) -> PaginaProveedores:
    total, elementos = repo.listar(
        sesion,
        region=region,
        tipo=tipo,
        busqueda=q,
        sin_region=sin_region,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return PaginaProveedores(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[ProveedorPublico.model_validate(p) for p in elementos],
    )


@router.get(
    "/opciones",
    summary="Regiones y tipos que tienen fichas cargadas",
)
def opciones(sesion: Session = Depends(get_db)) -> dict:
    """Alimenta el panel de filtros sin hardcodear la lista en el cliente."""
    return {
        "regiones": repo.regiones_disponibles(sesion),
        "tipos": repo.tipos_disponibles(sesion),
        "hay_sin_region": any(
            p.region is None
            for p in repo.listar(sesion, sin_region=True, limite=1)[1]
        ),
    }
