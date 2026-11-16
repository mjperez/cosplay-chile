"""Comunidad y foro (RF-22, 23, 27, 29) y desafíos mensuales (RF-36)."""
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.deps import DbSession, Gestor, UsuarioActual, UsuarioOpcional
from app.models.comunidad import DesafioMensual, Foro, ParticipacionDesafio, Respuesta, Tema
from app.patterns.observer import Eventos
from app.schemas.comun import AutorResumen, Pagina
from app.schemas.comunidad import (
    DesafioDetalle,
    DesafioOut,
    ForoOut,
    ParticipacionIn,
    ParticipacionOut,
    RespuestaIn,
    RespuestaOut,
    TemaDetalle,
    TemaIn,
    TemaResumen,
)

router = APIRouter(tags=["Comunidad y foro"])


# ------------------------------------------------------------------ foros
async def _foro(db, slug: str) -> Foro:
    foro = await db.scalar(select(Foro).where(Foro.slug == slug))
    if foro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foro no encontrado")
    return foro


def _foro_out(f: Foro, temas: int = 0, ultima=None) -> ForoOut:
    return ForoOut(id=f.id, titulo=f.titulo, slug=f.slug, categoria=f.categoria, temas=temas or 0, ultima_actividad=ultima)


@router.get("/api/foros", response_model=list[ForoOut], summary="Foros por temática (RF-22)")
async def foros(db: DbSession):
    agg = (select(Tema.foro_id, func.count().label("n"), func.max(Tema.created_at).label("ultima"))
           .where(Tema.oculto.is_(False)).group_by(Tema.foro_id).subquery())
    filas = (await db.execute(
        select(Foro, agg.c.n, agg.c.ultima).outerjoin(agg, agg.c.foro_id == Foro.id).order_by(Foro.orden, Foro.titulo)
    )).all()
    return [_foro_out(f, n, u) for f, n, u in filas]


def _resumenes(filas) -> list[TemaResumen]:
    return [
        TemaResumen(id=t.id, titulo=t.titulo, autor=AutorResumen.de(t.autor), created_at=t.created_at,
                    respuestas=n or 0, tiene_imagen=bool(t.imagen_url), foro_slug=t.foro.slug, foro_titulo=t.foro.titulo)
        for t, n in filas
    ]


def _conteo_respuestas():
    return (select(Respuesta.tema_id, func.count().label("n")).where(Respuesta.oculto.is_(False))
            .group_by(Respuesta.tema_id).subquery())


@router.get("/api/foros/{slug}/temas", response_model=Pagina[TemaResumen], summary="Temas de un foro")
async def temas(slug: str, db: DbSession, pagina: Annotated[int, Query(ge=1)] = 1,
                por_pagina: Annotated[int, Query(ge=1, le=50)] = 20):
    foro = await _foro(db, slug)
    filtros = [Tema.foro_id == foro.id, Tema.oculto.is_(False)]
    total = await db.scalar(select(func.count()).select_from(Tema).where(*filtros))
    resp = _conteo_respuestas()
    filas = (await db.execute(
        select(Tema, resp.c.n).outerjoin(resp, resp.c.tema_id == Tema.id).where(*filtros)
        .order_by(Tema.created_at.desc()).offset((pagina - 1) * por_pagina).limit(por_pagina)
    )).unique().all()
    return Pagina.crear(_resumenes(filas), total or 0, pagina, por_pagina)


@router.post("/api/foros/{slug}/temas", response_model=TemaDetalle, status_code=status.HTTP_201_CREATED,
             summary="Crear un tema (RF-23); foto opcional con créditos (RF-27)")
async def crear_tema(slug: str, datos: TemaIn, usuario: UsuarioActual, db: DbSession):
    foro = await _foro(db, slug)
    tema = Tema(foro_id=foro.id, autor_id=usuario.id, **datos.model_dump())
    tema.autor, tema.foro = usuario, foro
    db.add(tema)
    await db.commit()
    return await _detalle_tema(db, tema, usuario)


async def _detalle_tema(db, tema: Tema, usuario) -> TemaDetalle:
    filtros = [Respuesta.tema_id == tema.id]
    if not (usuario and usuario.es_admin):
        filtros.append(Respuesta.oculto.is_(False))
    respuestas = (await db.execute(select(Respuesta).where(*filtros).order_by(Respuesta.created_at))).scalars().all()
    return TemaDetalle(
        id=tema.id, titulo=tema.titulo, contenido=tema.contenido, autor=AutorResumen.de(tema.autor),
        created_at=tema.created_at, foro=_foro_out(tema.foro), imagen_url=tema.imagen_url, imagen_alt=tema.imagen_alt,
        credito_fotografo=tema.credito_fotografo, credito_cosplayer=tema.credito_cosplayer, oculto=tema.oculto,
        respuestas=[RespuestaOut(id=r.id, contenido=r.contenido, autor=AutorResumen.de(r.autor), created_at=r.created_at)
                    for r in respuestas],
    )


@router.get("/api/temas/recientes", response_model=list[TemaResumen], summary="Temas recientes de todos los foros")
async def temas_recientes(db: DbSession, limite: Annotated[int, Query(ge=1, le=20)] = 6):
    resp = _conteo_respuestas()
    filas = (await db.execute(
        select(Tema, resp.c.n).outerjoin(resp, resp.c.tema_id == Tema.id).where(Tema.oculto.is_(False))
        .order_by(Tema.created_at.desc()).limit(limite)
    )).unique().all()
    return _resumenes(filas)


@router.get("/api/temas/{tema_id}", response_model=TemaDetalle, summary="Tema con sus respuestas")
async def tema(tema_id: uuid.UUID, db: DbSession, usuario: UsuarioOpcional):
    t = await db.get(Tema, tema_id)
    if t is None or (t.oculto and not (usuario and usuario.es_admin)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tema no encontrado")
    return await _detalle_tema(db, t, usuario)


@router.post("/api/temas/{tema_id}/respuestas", response_model=RespuestaOut, status_code=status.HTTP_201_CREATED,
             summary="Responder un tema (RF-23)")
async def responder(tema_id: uuid.UUID, datos: RespuestaIn, usuario: UsuarioActual, db: DbSession, gestor: Gestor,
                    tareas: BackgroundTasks):
    t = await db.get(Tema, tema_id)
    if t is None or t.oculto:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tema no encontrado")
    r = Respuesta(tema_id=t.id, autor_id=usuario.id, contenido=datos.contenido)
    r.autor = usuario
    db.add(r)
    await db.commit()
    gestor.notificar_en_segundo_plano(
        tareas, Eventos.NUEVA_RESPUESTA,
        {"tema_id": t.id, "titulo": t.titulo, "autor_tema_id": t.autor_id, "autor_respuesta_id": usuario.id},
        actor_id=usuario.id,
    )
    return RespuestaOut(id=r.id, contenido=r.contenido, autor=AutorResumen.de(usuario), created_at=r.created_at)


# --------------------------------------------------------------- desafíos
def desafio_abierto(d: DesafioMensual) -> bool:
    """Se puede participar durante el mes del desafío (y antes, si se publica por adelantado)."""
    hoy = date.today()
    return (d.anio, d.mes) >= (hoy.year, hoy.month) and d.ganador_id is None


async def _conteo_participaciones(db, desafio_id) -> int:
    return await db.scalar(select(func.count()).select_from(ParticipacionDesafio).where(
        ParticipacionDesafio.desafio_id == desafio_id, ParticipacionDesafio.oculto.is_(False))) or 0


async def desafio_out(db, d: DesafioMensual) -> DesafioOut:
    return DesafioOut(id=d.id, titulo=d.titulo, descripcion=d.descripcion, mes=d.mes, anio=d.anio,
                      abierto=desafio_abierto(d), ganador=AutorResumen.de(d.ganador),
                      participaciones=await _conteo_participaciones(db, d.id))


@router.get("/api/desafios", response_model=list[DesafioOut], summary="Desafíos mensuales (RF-36)")
async def desafios(db: DbSession):
    filas = (await db.execute(select(DesafioMensual).order_by(DesafioMensual.anio.desc(), DesafioMensual.mes.desc())))
    return [await desafio_out(db, d) for d in filas.scalars().unique().all()]


@router.get("/api/desafios/{desafio_id}", response_model=DesafioDetalle, summary="Desafío con sus participaciones")
async def desafio(desafio_id: uuid.UUID, db: DbSession, usuario: UsuarioOpcional):
    d = await db.get(DesafioMensual, desafio_id)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Desafío no encontrado")
    parts = (await db.execute(
        select(ParticipacionDesafio).where(ParticipacionDesafio.desafio_id == d.id, ParticipacionDesafio.oculto.is_(False))
        .order_by(ParticipacionDesafio.created_at)
    )).scalars().unique().all()
    ganadora = next((p.id for p in parts if d.ganador_id and p.usuario_id == d.ganador_id), None)
    base = (await desafio_out(db, d)).model_dump()
    return DesafioDetalle(
        **base, ganador_participacion_id=ganadora,
        ya_participo=bool(usuario) and any(p.usuario_id == usuario.id for p in parts),
        lista_participaciones=[ParticipacionOut(
            id=p.id, titulo=p.titulo, descripcion=p.descripcion, autor=AutorResumen.de(p.usuario), imagen_url=p.imagen_url,
            imagen_alt=p.imagen_alt, credito_fotografo=p.credito_fotografo, credito_cosplayer=p.credito_cosplayer,
            created_at=p.created_at) for p in parts],
    )


@router.post("/api/desafios/{desafio_id}/participar", response_model=ParticipacionOut,
             status_code=status.HTTP_201_CREATED, summary="Participar en un desafío con una foto con créditos")
async def participar(desafio_id: uuid.UUID, datos: ParticipacionIn, usuario: UsuarioActual, db: DbSession):
    d = await db.get(DesafioMensual, desafio_id)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Desafío no encontrado")
    if not desafio_abierto(d):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este desafío ya cerró")
    p = ParticipacionDesafio(desafio_id=d.id, usuario_id=usuario.id, **datos.model_dump())
    p.usuario = usuario
    db.add(p)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya participaste en este desafío")
    return ParticipacionOut(id=p.id, titulo=p.titulo, descripcion=p.descripcion, autor=AutorResumen.de(usuario),
                            imagen_url=p.imagen_url, imagen_alt=p.imagen_alt, credito_fotografo=p.credito_fotografo,
                            credito_cosplayer=p.credito_cosplayer, created_at=p.created_at)
