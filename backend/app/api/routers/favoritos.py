"""Favoritos (RF-25): guías, proveedores/tiendas y eventos (interfaz Favoritable de la Fig. 11)."""
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.core.deps import DbSession, UsuarioActual
from app.models.contenido import Contenido
from app.models.directorio import DirectorioItem
from app.models.enums import EstadoPublicacion
from app.models.evento import Evento
from app.models.interaccion import Favorito
from app.schemas.comun import Mensaje

router = APIRouter(prefix="/api/favoritos", tags=["Favoritos"])

TipoFav = Literal["CONTENIDO", "DIRECTORIO", "EVENTO"]
COLUMNA = {"CONTENIDO": "contenido_id", "DIRECTORIO": "directorio_item_id", "EVENTO": "evento_id"}


class FavoritoIn(BaseModel):
    tipo: TipoFav
    objeto_id: uuid.UUID


class FavoritoOut(BaseModel):
    id: uuid.UUID
    tipo: TipoFav
    objeto_id: uuid.UUID
    titulo: str
    subtitulo: str = ""
    enlace: str
    imagen_url: str | None = None
    imagen_alt: str | None = None


async def _objeto_visible(db, tipo: str, objeto_id: uuid.UUID):
    if tipo == "CONTENIDO":
        o = await db.get(Contenido, objeto_id)
        return o if o and o.estado == EstadoPublicacion.PUBLICADO else None
    if tipo == "DIRECTORIO":
        o = await db.get(DirectorioItem, objeto_id)
        return o if o and o.activo else None
    o = await db.get(Evento, objeto_id)
    return o if o and o.estado == EstadoPublicacion.PUBLICADO else None


@router.get("", response_model=list[FavoritoOut], summary="Mis favoritos")
async def listar(usuario: UsuarioActual, db: DbSession):
    favs = (await db.execute(
        select(Favorito).where(Favorito.usuario_id == usuario.id).order_by(Favorito.created_at.desc())
    )).scalars().all()
    salida = []
    for f in favs:
        if f.contenido_id:
            c = await db.get(Contenido, f.contenido_id)
            salida.append(FavoritoOut(id=f.id, tipo="CONTENIDO", objeto_id=c.id, titulo=c.titulo,
                                      subtitulo=c.categoria.nombre, enlace=f"/guias/{c.id}",
                                      imagen_url=c.imagen_url, imagen_alt=c.imagen_alt))
        elif f.directorio_item_id:
            d = await db.get(DirectorioItem, f.directorio_item_id)
            salida.append(FavoritoOut(id=f.id, tipo="DIRECTORIO", objeto_id=d.id, titulo=d.nombre,
                                      subtitulo=d.comuna or "", enlace=f"/directorio/{d.id}",
                                      imagen_url=d.imagen_url, imagen_alt=d.imagen_alt))
        else:
            e = await db.get(Evento, f.evento_id)
            salida.append(FavoritoOut(id=f.id, tipo="EVENTO", objeto_id=e.id, titulo=e.nombre,
                                      subtitulo=f"{e.fecha_inicio:%d-%m-%Y} · {e.lugar}", enlace=f"/calendario/{e.id}",
                                      imagen_url=e.imagen_url, imagen_alt=e.imagen_alt))
    return salida


@router.get("/ids", summary="Ids de mis favoritos por tipo (para marcar botones)")
async def ids(usuario: UsuarioActual, db: DbSession) -> dict[str, list[str]]:
    favs = (await db.execute(select(Favorito).where(Favorito.usuario_id == usuario.id))).scalars().all()
    r = {"CONTENIDO": [], "DIRECTORIO": [], "EVENTO": []}
    for f in favs:
        for tipo, col in COLUMNA.items():
            if getattr(f, col):
                r[tipo].append(str(getattr(f, col)))
    return r


@router.post("", response_model=Mensaje, status_code=status.HTTP_201_CREATED, summary="Guardar en favoritos")
async def agregar(datos: FavoritoIn, usuario: UsuarioActual, db: DbSession):
    if await _objeto_visible(db, datos.tipo, datos.objeto_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos lo que quieres guardar")
    db.add(Favorito(usuario_id=usuario.id, **{COLUMNA[datos.tipo]: datos.objeto_id}))
    try:
        await db.commit()
    except IntegrityError:  # ya estaba guardado: operación idempotente
        await db.rollback()
    return Mensaje(mensaje="Guardado en tus favoritos")


@router.delete("/{tipo}/{objeto_id}", response_model=Mensaje, summary="Quitar de favoritos")
async def quitar(tipo: TipoFav, objeto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    await db.execute(delete(Favorito).where(
        Favorito.usuario_id == usuario.id, getattr(Favorito, COLUMNA[tipo]) == objeto_id))
    await db.commit()
    return Mensaje(mensaje="Quitado de tus favoritos")
