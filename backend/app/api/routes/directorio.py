"""Complementos del directorio: dónde comprar y grupos de la comunidad."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import directorio as repo
from app.schemas.directorio import GrupoPublico, PaginaGrupos, PaginaTiendas, TiendaPublica

router = APIRouter(tags=["directorio"])


@router.get("/tiendas", response_model=PaginaTiendas, summary="Tiendas de materiales")
def listar_tiendas(
    tipo: str | None = Query(None, description="telas, insumos, pelucas, impresion_3d u otro"),
    region: str | None = Query(None),
    q: str | None = Query(None, max_length=80),
    limite: int = Query(50, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
) -> PaginaTiendas:
    total, elementos = repo.listar_tiendas(
        sesion,
        tipo=tipo,
        region=region,
        busqueda=q,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return PaginaTiendas(
        total=total,
        elementos=[TiendaPublica.model_validate(t) for t in elementos],
    )


@router.get("/grupos", response_model=PaginaGrupos, summary="Grupos y comunidades")
def listar_grupos(
    region: str | None = Query(None),
    plataforma: str | None = Query(None, description="facebook, discord, instagram, whatsapp, foro u otro"),
    limite: int = Query(50, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
) -> PaginaGrupos:
    total, elementos = repo.listar_grupos(
        sesion,
        region=region,
        plataforma=plataforma,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return PaginaGrupos(
        total=total,
        elementos=[GrupoPublico.model_validate(g) for g in elementos],
    )
