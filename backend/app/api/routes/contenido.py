"""Contenido editorial: guías, entrevistas y artículos (US-08)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual, requiere_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.repositories import contenido as repo
from app.schemas.contenido import (
    CategoriaEntrada,
    CategoriaPublica,
    ContenidoEntrada,
    ContenidoPublico,
    PaginaContenido,
)
from app.services import contenido as servicio

router = APIRouter(prefix="/contenido", tags=["contenido"])

# Órdenes de ruta: `/categorias` va antes que `/{id_contenido}`. Si estuviera
# después, FastAPI intentaría convertir "categorias" en un UUID y devolvería
# 422 en lugar de entrar al endpoint.


@router.get(
    "/categorias",
    response_model=list[CategoriaPublica],
    summary="Categorías de contenido disponibles",
)
def listar_categorias(sesion: Session = Depends(get_db)) -> list:
    return repo.listar_categorias(sesion)


@router.post(
    "/categorias",
    response_model=CategoriaPublica,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una categoría (solo administrador)",
    dependencies=[Depends(requiere_admin)],
)
def crear_categoria(datos: CategoriaEntrada, sesion: Session = Depends(get_db)) -> object:
    try:
        return servicio.crear_categoria(
            sesion, nombre=datos.nombre, descripcion=datos.descripcion
        )
    except servicio.CategoriaDuplicada as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"la categoría «{error.nombre}» ya existe",
        )


@router.get(
    "",
    response_model=PaginaContenido,
    summary="Listar contenido publicado",
)
def listar_contenido(
    tipo: str | None = Query(None, description="guia, entrevista o articulo"),
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
) -> PaginaContenido:
    total, elementos = servicio.listar_publicos(
        sesion, tipo=tipo, limite=limite, desplazamiento=desplazamiento
    )
    return PaginaContenido(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[ContenidoPublico.model_validate(c) for c in elementos],
    )


@router.post(
    "",
    response_model=ContenidoPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un contenido en borrador",
)
def crear_contenido(
    datos: ContenidoEntrada,
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> object:
    try:
        contenido = servicio.crear(sesion, datos, usuario)
    except servicio.CategoriaInexistente as error:
        raise HTTPException(
            status_code=422,
            detail=f"la categoría {error.id_categoria} no existe",
        )
    return ContenidoPublico.model_validate(contenido)


@router.get(
    "/{id_contenido}",
    response_model=ContenidoPublico,
    summary="Ver un contenido publicado",
)
def obtener_contenido(
    id_contenido: uuid.UUID, sesion: Session = Depends(get_db)
) -> object:
    try:
        contenido = servicio.obtener_publico(sesion, id_contenido)
    except servicio.ContenidoNoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="contenido no encontrado"
        )
    return ContenidoPublico.model_validate(contenido)


@router.post(
    "/{id_contenido}/publicar",
    response_model=ContenidoPublico,
    summary="Publicar un borrador (solo administrador)",
    dependencies=[Depends(requiere_admin)],
)
def publicar_contenido(
    id_contenido: uuid.UUID, sesion: Session = Depends(get_db)
) -> object:
    try:
        contenido = servicio.publicar(sesion, id_contenido)
    except servicio.ContenidoNoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="contenido no encontrado"
        )
    except servicio.PublicacionInvalida as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"no se puede publicar un contenido en estado «{error.estado}»",
        )
    return ContenidoPublico.model_validate(contenido)
