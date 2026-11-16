"""Portada (RF-01): novedades del ecosistema y estadísticas de la comunidad."""
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import distinct, func, select

from app.api.routers.comunidad import desafio_abierto, desafio_out
from app.core.deps import DbSession
from app.models.comunidad import DesafioMensual, ParticipacionDesafio, Respuesta, Tema
from app.models.contenido import Contenido
from app.models.directorio import DirectorioItem
from app.models.enums import EstadoPublicacion, EstadoUsuario, TipoDirectorio
from app.models.evento import Evento
from app.models.usuario import Usuario
from app.schemas.comun import AutorResumen
from app.schemas.comunidad import DesafioOut, ParticipacionOut, TemaResumen
from app.schemas.contenido import ContenidoResumen
from app.schemas.evento import EventoOut

router = APIRouter(prefix="/api/inicio", tags=["Inicio y búsqueda"])


class Estadisticas(BaseModel):
    personas: int
    guias: int
    proveedores: int
    tiendas: int
    comunidades: int
    eventos_proximos: int
    temas: int
    regiones_con_presencia: int


class Portada(BaseModel):
    estadisticas: Estadisticas
    ultimas_guias: list[ContenidoResumen]
    proximos_eventos: list[EventoOut]
    temas_destacados: list[TemaResumen]
    trajes_recientes: list[ParticipacionOut]
    desafio_actual: DesafioOut | None


@router.get("", response_model=Portada, summary="Datos de la portada")
async def portada(db: DbSession):
    hoy = date.today()

    async def contar(stmt) -> int:
        return await db.scalar(stmt) or 0

    dir_activo = DirectorioItem.activo.is_(True)
    est = Estadisticas(
        personas=await contar(select(func.count()).select_from(Usuario).where(Usuario.estado == EstadoUsuario.ACTIVO)),
        guias=await contar(select(func.count()).select_from(Contenido).where(Contenido.estado == EstadoPublicacion.PUBLICADO)),
        proveedores=await contar(select(func.count()).select_from(DirectorioItem).where(dir_activo, DirectorioItem.tipo == TipoDirectorio.PROVEEDOR)),
        tiendas=await contar(select(func.count()).select_from(DirectorioItem).where(dir_activo, DirectorioItem.tipo == TipoDirectorio.TIENDA)),
        comunidades=await contar(select(func.count()).select_from(DirectorioItem).where(dir_activo, DirectorioItem.tipo == TipoDirectorio.COMUNIDAD)),
        eventos_proximos=await contar(select(func.count()).select_from(Evento).where(
            Evento.estado == EstadoPublicacion.PUBLICADO, Evento.fecha_inicio >= hoy)),
        temas=await contar(select(func.count()).select_from(Tema).where(Tema.oculto.is_(False))),
        regiones_con_presencia=await contar(select(func.count(distinct(DirectorioItem.region))).where(
            dir_activo, DirectorioItem.region.is_not(None))),
    )

    guias = (await db.execute(select(Contenido).where(Contenido.estado == EstadoPublicacion.PUBLICADO)
                              .order_by(Contenido.publicado_at.desc().nulls_last()).limit(4))).scalars().unique().all()
    eventos = (await db.execute(select(Evento).where(Evento.estado == EstadoPublicacion.PUBLICADO, Evento.fecha_inicio >= hoy)
                                .order_by(Evento.fecha_inicio).limit(4))).scalars().unique().all()

    # Hilos destacados: más respuestas en los últimos 30 días
    desde = datetime.now(timezone.utc) - timedelta(days=30)
    resp = (select(Respuesta.tema_id, func.count().label("n")).where(Respuesta.oculto.is_(False), Respuesta.created_at >= desde)
            .group_by(Respuesta.tema_id).subquery())
    filas = (await db.execute(select(Tema, resp.c.n).join(resp, resp.c.tema_id == Tema.id).where(Tema.oculto.is_(False))
                              .order_by(resp.c.n.desc(), Tema.created_at.desc()).limit(4))).unique().all()
    temas = [TemaResumen(id=t.id, titulo=t.titulo, autor=AutorResumen.de(t.autor), created_at=t.created_at, respuestas=n,
                         tiene_imagen=bool(t.imagen_url), foro_slug=t.foro.slug, foro_titulo=t.foro.titulo) for t, n in filas]

    # Trajes recientes: fotos con créditos de los desafíos
    parts = (await db.execute(select(ParticipacionDesafio).where(ParticipacionDesafio.oculto.is_(False))
                              .order_by(ParticipacionDesafio.created_at.desc()).limit(4))).scalars().unique().all()
    trajes = [ParticipacionOut(id=p.id, titulo=p.titulo, descripcion=p.descripcion, autor=AutorResumen.de(p.usuario),
                               imagen_url=p.imagen_url, imagen_alt=p.imagen_alt, credito_fotografo=p.credito_fotografo,
                               credito_cosplayer=p.credito_cosplayer, created_at=p.created_at) for p in parts]

    desafios = (await db.execute(select(DesafioMensual).order_by(DesafioMensual.anio, DesafioMensual.mes))).scalars().unique().all()
    actual = next((d for d in desafios if desafio_abierto(d)), None)

    return Portada(
        estadisticas=est,
        ultimas_guias=[ContenidoResumen.de(c) for c in guias],
        proximos_eventos=[EventoOut.de(e) for e in eventos],
        temas_destacados=temas,
        trajes_recientes=trajes,
        desafio_actual=await desafio_out(db, actual) if actual else None,
    )
