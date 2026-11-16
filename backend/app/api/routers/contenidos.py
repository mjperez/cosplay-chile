"""Módulo Contenidos Educativos (RF-02, 03, 04, 06, 18, 20, 21, 24, 28, 39)."""
import re
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from app.core.deps import DbSession, Gestor, UsuarioActual, UsuarioOpcional
from app.models.contenido import CategoriaContenido, Contenido
from app.models.enums import Nivel, TipoContenido
from app.models.interaccion import Favorito
from app.schemas.comun import Pagina
from app.schemas.contenido import CategoriaOut, ContenidoCrear, ContenidoCreado, ContenidoDetalle, ContenidoResumen
from app.services import contenido_service

router = APIRouter(tags=["Contenidos educativos"])


@router.get("/api/categorias", response_model=list[CategoriaOut], summary="Categorías temáticas")
async def categorias(db: DbSession):
    return (await db.execute(select(CategoriaContenido).order_by(CategoriaContenido.nombre))).scalars().all()


@router.get("/api/contenidos", response_model=Pagina[ContenidoResumen],
            summary="Listar guías, entrevistas y artículos publicados (filtros por nivel y categoría)")
async def listar(
    db: DbSession,
    nivel: Nivel | None = None,
    categoria: Annotated[str | None, Query(description="slug de la categoría")] = None,
    tipo: TipoContenido | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=50)] = 12,
):
    filas, total = await contenido_service.listar_publicados(
        db, nivel=nivel, categoria=categoria, tipo=tipo, q=q, pagina=pagina, por_pagina=por_pagina
    )
    return Pagina.crear([ContenidoResumen.de(c) for c in filas], total, pagina, por_pagina)


@router.get("/api/contenidos/mios", response_model=list[ContenidoResumen], summary="Mis envíos y su estado")
async def mis_envios(usuario: UsuarioActual, db: DbSession):
    filas = (await db.execute(
        select(Contenido).where(Contenido.autor_id == usuario.id).order_by(Contenido.created_at.desc())
    )).scalars().unique().all()
    return [ContenidoResumen.de(c) for c in filas]


@router.post("/api/contenidos", response_model=ContenidoCreado, status_code=status.HTTP_201_CREATED,
             responses={422: {"description": "Categoría no encontrada o datos inválidos"}},
             summary="Publicar un tutorial (UC6): queda pendiente de revisión")
async def publicar(datos: ContenidoCrear, usuario: UsuarioActual, db: DbSession, gestor: Gestor,
                   tareas: BackgroundTasks):
    c = await contenido_service.publicar_tutorial(db, gestor, tareas, usuario, datos)
    return ContenidoCreado(
        mensaje="¡Gracias! Tu contenido fue enviado y está en revisión. Te avisaremos cuando se publique.",
        contenido=ContenidoDetalle.de(c),
    )


@router.get("/api/contenidos/{contenido_id}", response_model=ContenidoDetalle, summary="Detalle de un contenido")
async def detalle(contenido_id: uuid.UUID, db: DbSession, usuario: UsuarioOpcional):
    c = await contenido_service.obtener_visible(db, contenido_id, usuario)
    favorito = False
    if usuario:
        favorito = await db.scalar(select(Favorito.id).where(
            Favorito.usuario_id == usuario.id, Favorito.contenido_id == c.id)) is not None
    return ContenidoDetalle.de(c, es_favorito=favorito)


@router.get("/api/contenidos/{contenido_id}/descargar", response_class=HTMLResponse,
            summary="Descargar el contenido (RF-06, solo con sesión)")
async def descargar(contenido_id: uuid.UUID, db: DbSession, usuario: UsuarioActual):
    c = await contenido_service.obtener_visible(db, contenido_id, usuario)
    nombre = re.sub(r"[^a-z0-9]+", "-", c.titulo.lower()).strip("-")[:60] or "contenido"
    return HTMLResponse(
        contenido_service.html_descarga(c),
        headers={"Content-Disposition": f'attachment; filename="cosplaychile-{nombre}.html"'},
    )
