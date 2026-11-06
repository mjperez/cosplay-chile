"""Endpoints de administración. Todos exigen rol `administrador`."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import requiere_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.repositories import contenido as repo_contenido
from app.repositories import usuario as repo_usuarios
from app.schemas.auth import PaginaUsuarios, UsuarioPublico
from app.schemas.contenido import ContenidoPublico, PaginaContenido

# La dependencia va en el router, no en cada endpoint: si mañana se agrega una
# ruta acá, ya nace protegida.
router = APIRouter(
    prefix="/admin",
    tags=["administración"],
    dependencies=[Depends(requiere_admin)],
)


@router.get(
    "/usuarios",
    response_model=PaginaUsuarios,
    summary="Listar cuentas registradas",
)
def listar_usuarios(
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
) -> PaginaUsuarios:
    total = repo_usuarios.contar(sesion)
    elementos = repo_usuarios.listar(
        sesion, limite=limite, desplazamiento=desplazamiento
    )
    return PaginaUsuarios(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[UsuarioPublico.model_validate(u) for u in elementos],
    )


@router.get(
    "/contenido",
    response_model=PaginaContenido,
    summary="Listar contenido en cualquier estado, incluidos los borradores",
)
def listar_contenido(
    estado: str | None = Query(None, description="pendiente, publicado o rechazado"),
    tipo: str | None = Query(None, description="guia, entrevista o articulo"),
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
) -> PaginaContenido:
    """La bandeja editorial. Es el único lugar donde se ven los borradores."""
    total, elementos = repo_contenido.listar(
        sesion,
        estado=estado,
        tipo=tipo,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return PaginaContenido(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[ContenidoPublico.model_validate(c) for c in elementos],
    )
