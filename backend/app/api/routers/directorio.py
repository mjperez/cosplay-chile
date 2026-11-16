"""Directorio de profesionales, tiendas y comunidades (RF-11 a 14, 19, 32 a 34)."""
import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.core.deps import DbSession, UsuarioActual, UsuarioOpcional
from app.models.directorio import DirectorioItem, Resena
from app.models.enums import REGION_CENTRO, AlcanceTienda, Especialidad, Region, TipoDirectorio, TipoProducto
from app.models.interaccion import Favorito
from app.schemas.comun import Pagina
from app.schemas.directorio import (
    DirectorioDetalle,
    DirectorioResumen,
    MiFichaUpdate,
    PuntoMapa,
    ResenaIn,
    ResenaOut,
)
from app.services.busqueda_util import coincide

router = APIRouter(prefix="/api/directorio", tags=["Directorio"])


def _agregado_resenas():
    return (
        select(Resena.directorio_item_id.label("iid"), func.avg(Resena.calificacion).label("prom"),
               func.count().label("n"))
        .where(Resena.oculta.is_(False)).group_by(Resena.directorio_item_id).subquery()
    )


def _filtros(tipo, region, especialidad, tipo_producto, alcance, q):
    f = [DirectorioItem.activo.is_(True)]
    if tipo:
        f.append(DirectorioItem.tipo == tipo)
    if region:
        f.append(DirectorioItem.region == region)
    if especialidad:
        f.append(DirectorioItem.especialidades.contains([especialidad.value]))
    if tipo_producto:
        f.append(DirectorioItem.tipos_producto.contains([tipo_producto.value]))
    if alcance:
        f.append(DirectorioItem.alcance == alcance)
    if q:
        f.append(or_(coincide(DirectorioItem.nombre, q), coincide(DirectorioItem.descripcion, q),
                     coincide(DirectorioItem.comuna, q)))
    return f


@router.get("", response_model=Pagina[DirectorioResumen], summary="Buscar en el directorio (filtros por región y especialidad)")
async def listar(
    db: DbSession,
    tipo: TipoDirectorio | None = None,
    region: Region | None = None,
    especialidad: Especialidad | None = None,
    tipo_producto: TipoProducto | None = None,
    alcance: AlcanceTienda | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=50)] = 12,
):
    filtros = _filtros(tipo, region, especialidad, tipo_producto, alcance, q)
    agg = _agregado_resenas()
    total = await db.scalar(select(func.count()).select_from(DirectorioItem).where(*filtros))
    filas = (await db.execute(
        select(DirectorioItem, agg.c.prom, agg.c.n).outerjoin(agg, agg.c.iid == DirectorioItem.id)
        .where(*filtros)
        .order_by(func.coalesce(agg.c.prom, 0).desc(), DirectorioItem.nombre)
        .offset((pagina - 1) * por_pagina).limit(por_pagina)
    )).unique().all()
    return Pagina.crear([DirectorioResumen.de(i, p, n) for i, p, n in filas], total or 0, pagina, por_pagina)


@router.get("/mapa", response_model=list[PuntoMapa], summary="Puntos para el mapa interactivo de Chile (RF-12)")
async def mapa(
    db: DbSession,
    tipo: TipoDirectorio | None = None,
    region: Region | None = None,
    especialidad: Especialidad | None = None,
    tipo_producto: TipoProducto | None = None,
):
    filtros = _filtros(tipo, region, especialidad, tipo_producto, None, None)
    filas = (await db.execute(
        select(DirectorioItem).where(*filtros, DirectorioItem.lat.is_not(None), DirectorioItem.lng.is_not(None))
        .order_by(DirectorioItem.nombre).limit(500)
    )).scalars().unique().all()
    return [
        PuntoMapa(id=i.id, tipo=i.tipo, nombre=i.nombre, lat=i.lat, lng=i.lng, region=i.region, comuna=i.comuna,
                  detalle=", ".join((i.especialidades or i.tipos_producto or [i.plataforma or ""])[:3]))
        for i in filas
    ]


async def _detalle(db, item: DirectorioItem, usuario) -> DirectorioDetalle:
    resenas = (await db.execute(
        select(Resena).where(Resena.directorio_item_id == item.id, Resena.oculta.is_(False))
        .order_by(Resena.created_at.desc())
    )).scalars().all()
    promedio = sum(r.calificacion for r in resenas) / len(resenas) if resenas else None
    base = DirectorioResumen.de(item, promedio, len(resenas)).model_dump()
    es_fav = ya = False
    if usuario:
        es_fav = await db.scalar(select(Favorito.id).where(
            Favorito.usuario_id == usuario.id, Favorito.directorio_item_id == item.id)) is not None
        ya = any(r.usuario_id == usuario.id for r in resenas) or await db.scalar(select(Resena.id).where(
            Resena.usuario_id == usuario.id, Resena.directorio_item_id == item.id)) is not None
    return DirectorioDetalle(
        **base, servicios=item.servicios, portafolio=item.portafolio, contacto=item.contacto,
        sitio_web=item.sitio_web, direccion=item.direccion,
        perfil_usuario_id=item.usuario_id if item.usuario and item.usuario.perfil.perfil_publico else None,
        resenas=[ResenaOut.de(r) for r in resenas], es_favorito=es_fav,
        puede_resenar=bool(usuario) and item.tipo != TipoDirectorio.COMUNIDAD and item.usuario_id != usuario.id
        if usuario else False,
        ya_resenado=ya,
    )


@router.get("/mi-ficha", response_model=DirectorioDetalle, summary="Mi ficha en el directorio (si activé el perfil público)")
async def mi_ficha(usuario: UsuarioActual, db: DbSession):
    item = await db.scalar(select(DirectorioItem).where(DirectorioItem.usuario_id == usuario.id))
    if item is None or not item.activo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No tienes una ficha activa en el directorio")
    return await _detalle(db, item, usuario)


@router.put("/mi-ficha", response_model=DirectorioDetalle, summary="Completar mi ficha: servicios, precios, portafolio (RF-32)")
async def actualizar_mi_ficha(datos: MiFichaUpdate, usuario: UsuarioActual, db: DbSession):
    item = await db.scalar(select(DirectorioItem).where(DirectorioItem.usuario_id == usuario.id))
    if item is None or not item.activo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Activa tu perfil público para tener una ficha en el directorio")
    cambios = datos.model_dump(exclude_unset=True, mode="json")
    es_tienda = item.tipo == TipoDirectorio.TIENDA
    campos_tienda = {"tipos_producto", "alcance", "tienda_fisica"}
    campos_proveedor = {"servicios", "especialidades", "precio_desde", "precio_hasta"}
    for campo, valor in cambios.items():
        if (es_tienda and campo in campos_proveedor) or (not es_tienda and campo in campos_tienda):
            continue
        setattr(item, campo, valor)
    if "region" in cambios and item.region and (item.lat is None or "comuna" in cambios):
        item.lat, item.lng = REGION_CENTRO[Region(item.region)]
    await db.commit()
    await db.refresh(item)
    return await _detalle(db, item, usuario)


@router.get("/{item_id}", response_model=DirectorioDetalle, summary="Ficha de un proveedor, tienda o comunidad")
async def detalle(item_id: uuid.UUID, db: DbSession, usuario: UsuarioOpcional):
    item = await db.get(DirectorioItem, item_id)
    if item is None or not item.activo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ficha no encontrada")
    return await _detalle(db, item, usuario)


@router.post("/{item_id}/resenas", response_model=ResenaOut, status_code=status.HTTP_201_CREATED,
             summary="Dejar una reseña (RF-19, requiere sesión)")
async def resenar(item_id: uuid.UUID, datos: ResenaIn, usuario: UsuarioActual, db: DbSession):
    item = await db.get(DirectorioItem, item_id)
    if item is None or not item.activo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ficha no encontrada")
    if item.tipo == TipoDirectorio.COMUNIDAD:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Las comunidades no reciben calificaciones")
    if item.usuario_id == usuario.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes calificar tu propia ficha")
    resena = Resena(usuario_id=usuario.id, directorio_item_id=item.id, **datos.model_dump())
    resena.usuario = usuario
    db.add(resena)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya dejaste una reseña para esta ficha")
    return ResenaOut.de(resena)
