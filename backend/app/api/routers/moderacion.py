"""Panel de moderación (solo Administrador/Moderador): revisión editorial, eventos sugeridos,
reportes, sanciones, contacto, desafíos y bitácora (Fig. 10, RF-17, 24, 36, 38, 40)."""
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.routers.comunidad import desafio_out
from app.core.deps import Admin, DbSession, Gestor
from app.models.comunidad import DesafioMensual, ParticipacionDesafio
from app.models.contenido import Contenido
from app.models.enums import EstadoContacto, EstadoPublicacion, EstadoReporte, EstadoUsuario
from app.models.evento import Evento
from app.models.interaccion import Contacto, RegistroAuditoria, Reporte
from app.models.usuario import Usuario
from app.patterns.observer import Eventos
from app.schemas.comun import AutorResumen, Mensaje
from app.schemas.comunidad import DesafioIn, DesafioOut, GanadorIn
from app.schemas.contenido import ContenidoDetalle, Rechazo
from app.schemas.evento import EventoOut
from app.schemas.moderacion import (
    AuditoriaOut,
    ContactoOut,
    ReporteOut,
    ResolverReporteIn,
    ResumenModeracion,
    SuspensionIn,
    UsuarioAdminOut,
)
from app.services import contenido_service, moderacion_service as ms

router = APIRouter(prefix="/api/moderacion", tags=["Moderación y seguridad"])


@router.get("/contenidos", response_model=list[ContenidoDetalle], summary="Cola de revisión de contenidos")
async def cola_contenidos(admin: Admin, db: DbSession, estado: EstadoPublicacion = EstadoPublicacion.PENDIENTE):
    filas = (await db.execute(
        select(Contenido).where(Contenido.estado == estado).order_by(Contenido.created_at)
    )).scalars().unique().all()
    return [ContenidoDetalle.de(c) for c in filas]


@router.post("/contenidos/{contenido_id}/publicar", response_model=ContenidoDetalle, summary="Aprobar y publicar")
async def publicar(contenido_id: uuid.UUID, admin: Admin, db: DbSession, gestor: Gestor, tareas: BackgroundTasks):
    c = await contenido_service.moderar(db, gestor, tareas, admin, contenido_id, aprobar=True)
    return ContenidoDetalle.de(c)


@router.post("/contenidos/{contenido_id}/rechazar", response_model=ContenidoDetalle, summary="Rechazar con motivo")
async def rechazar(contenido_id: uuid.UUID, datos: Rechazo, admin: Admin, db: DbSession, gestor: Gestor,
                   tareas: BackgroundTasks):
    c = await contenido_service.moderar(db, gestor, tareas, admin, contenido_id, aprobar=False, motivo=datos.motivo)
    return ContenidoDetalle.de(c)


# ---------------------------------------------------------------- Eventos sugeridos (RF-17)
@router.get("/eventos", response_model=list[EventoOut], summary="Eventos sugeridos pendientes")
async def eventos_pendientes(admin: Admin, db: DbSession):
    filas = (await db.execute(
        select(Evento).where(Evento.estado == EstadoPublicacion.PENDIENTE).order_by(Evento.created_at)
    )).scalars().unique().all()
    return [EventoOut.de(e) for e in filas]


@router.post("/eventos/{evento_id}/{decision}", response_model=EventoOut, summary="Aprobar o rechazar un evento sugerido")
async def decidir_evento(evento_id: uuid.UUID, decision: Literal["aprobar", "rechazar"], admin: Admin, db: DbSession,
                         gestor: Gestor, tareas: BackgroundTasks):
    e = await db.get(Evento, evento_id)
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")
    if e.estado != EstadoPublicacion.PENDIENTE:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este evento ya fue revisado")
    aprobar = decision == "aprobar"
    e.estado = EstadoPublicacion.PUBLICADO if aprobar else EstadoPublicacion.RECHAZADO
    await db.commit()
    gestor.notificar_en_segundo_plano(
        tareas, Eventos.EVENTO_PUBLICADO if aprobar else Eventos.EVENTO_RECHAZADO,
        {"evento_id": e.id, "nombre": e.nombre, "autor_id": e.creado_por_id if e.creado_por_id != admin.id else None},
        actor_id=admin.id,
    )
    return EventoOut.de(e)


# ---------------------------------------------------------------- Resumen
@router.get("/resumen", response_model=ResumenModeracion, summary="Pendientes del panel")
async def resumen(admin: Admin, db: DbSession):
    async def contar(modelo, *cond):
        return await db.scalar(select(func.count()).select_from(modelo).where(*cond)) or 0
    return ResumenModeracion(
        contenidos_pendientes=await contar(Contenido, Contenido.estado == EstadoPublicacion.PENDIENTE),
        eventos_pendientes=await contar(Evento, Evento.estado == EstadoPublicacion.PENDIENTE),
        reportes_abiertos=await contar(Reporte, Reporte.estado == EstadoReporte.ABIERTO),
        contactos_nuevos=await contar(Contacto, Contacto.estado == EstadoContacto.NUEVO),
    )


# ---------------------------------------------------------------- Reportes (RF-38)
async def _reporte_out(db, r: Reporte) -> ReporteOut:
    obj = await db.get(ms.MODELOS[r.tipo_objeto], r.objeto_id)
    resumen_obj = ms.resumen_objeto(r.tipo_objeto, obj)
    autor = await db.get(Usuario, ms.autor_de(r.tipo_objeto, obj)) if obj and ms.autor_de(r.tipo_objeto, obj) else None
    return ReporteOut(
        id=r.id, tipo_objeto=r.tipo_objeto, objeto_id=r.objeto_id, motivo=r.motivo, detalle=r.detalle, estado=r.estado,
        resolucion=r.resolucion, created_at=r.created_at, resuelto_at=r.resuelto_at,
        reportante=AutorResumen.de(r.reportante), objeto_texto=resumen_obj["texto"],
        objeto_enlace=resumen_obj["enlace"], objeto_oculto=resumen_obj["oculto"],
        autor_objeto=AutorResumen.de(autor), autor_objeto_estado=autor.estado if autor else None,
    )


@router.get("/reportes", response_model=list[ReporteOut], summary="Reportes de la comunidad")
async def reportes(admin: Admin, db: DbSession, estado: EstadoReporte = EstadoReporte.ABIERTO):
    filas = (await db.execute(
        select(Reporte).where(Reporte.estado == estado).order_by(Reporte.created_at.desc()).limit(200)
    )).scalars().unique().all()
    return [await _reporte_out(db, r) for r in filas]


@router.post("/reportes/{reporte_id}/resolver", response_model=ReporteOut,
             summary="Resolver un reporte: descartar, resolver, ocultar u ocultar y suspender al autor")
async def resolver_reporte(reporte_id: uuid.UUID, datos: ResolverReporteIn, admin: Admin, db: DbSession,
                           gestor: Gestor, tareas: BackgroundTasks):
    r = await db.get(Reporte, reporte_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reporte no encontrado")
    await ms.resolver_reporte(db, gestor, tareas, admin, r, datos.accion, datos.resolucion)
    return await _reporte_out(db, r)


# ---------------------------------------------------------------- Usuarios (Bloquear/Sancionar)
def _usuario_out(u: Usuario) -> UsuarioAdminOut:
    return UsuarioAdminOut(id=u.id, nombre=u.nombre, email=u.email, rol=u.rol, estado=u.estado,
                           tipo_perfil=u.perfil.tipo_perfil if u.perfil else None,
                           motivo_suspension=u.motivo_suspension, created_at=u.created_at)


@router.get("/usuarios", response_model=list[UsuarioAdminOut], summary="Buscar cuentas")
async def usuarios(admin: Admin, db: DbSession, q: Annotated[str | None, Query(max_length=100)] = None,
                   estado: EstadoUsuario | None = None):
    filtros = [Usuario.estado != EstadoUsuario.ELIMINADO]
    if estado:
        filtros.append(Usuario.estado == estado)
    if q:
        patron = f"%{q.strip().lower()}%"
        filtros.append(or_(func.lower(Usuario.nombre).like(patron), func.lower(Usuario.email).like(patron)))
    filas = (await db.execute(select(Usuario).where(*filtros).order_by(Usuario.nombre).limit(100))).scalars().all()
    return [_usuario_out(u) for u in filas]


@router.post("/usuarios/{usuario_id}/suspender", response_model=UsuarioAdminOut, summary="Suspender una cuenta")
async def suspender(usuario_id: uuid.UUID, datos: SuspensionIn, admin: Admin, db: DbSession, gestor: Gestor,
                    tareas: BackgroundTasks):
    u = await db.get(Usuario, usuario_id)
    if u is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    await ms.suspender(db, admin, u, datos.motivo)
    await db.commit()
    gestor.notificar_en_segundo_plano(tareas, Eventos.USUARIO_SUSPENDIDO,
                                      {"usuario_id": u.id, "motivo": datos.motivo}, actor_id=admin.id)
    return _usuario_out(u)


@router.post("/usuarios/{usuario_id}/reactivar", response_model=UsuarioAdminOut, summary="Reactivar una cuenta suspendida")
async def reactivar(usuario_id: uuid.UUID, admin: Admin, db: DbSession, gestor: Gestor, tareas: BackgroundTasks):
    u = await db.get(Usuario, usuario_id)
    if u is None or u.estado != EstadoUsuario.SUSPENDIDO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La cuenta no está suspendida")
    u.estado, u.motivo_suspension = EstadoUsuario.ACTIVO, None
    await db.commit()
    gestor.notificar_en_segundo_plano(tareas, Eventos.USUARIO_REACTIVADO, {"usuario_id": u.id}, actor_id=admin.id)
    return _usuario_out(u)


# ---------------------------------------------------------------- Contacto (RF-40)
@router.get("/contactos", response_model=list[ContactoOut], summary="Mensajes del formulario de contacto")
async def contactos(admin: Admin, db: DbSession, estado: EstadoContacto = EstadoContacto.NUEVO):
    return (await db.execute(
        select(Contacto).where(Contacto.estado == estado).order_by(Contacto.created_at.desc()).limit(200)
    )).scalars().all()


@router.post("/contactos/{contacto_id}/atender", response_model=Mensaje, summary="Marcar un mensaje como atendido")
async def atender(contacto_id: uuid.UUID, admin: Admin, db: DbSession):
    c = await db.get(Contacto, contacto_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mensaje no encontrado")
    c.estado = EstadoContacto.ATENDIDO
    await db.commit()
    return Mensaje(mensaje="Mensaje marcado como atendido")


# ---------------------------------------------------------------- Desafíos mensuales (RF-36)
@router.post("/desafios", response_model=DesafioOut, status_code=status.HTTP_201_CREATED,
             summary="Lanzar un desafío mensual (notifica a la comunidad)")
async def crear_desafio(datos: DesafioIn, admin: Admin, db: DbSession, gestor: Gestor, tareas: BackgroundTasks):
    if await db.scalar(select(DesafioMensual.id).where(DesafioMensual.mes == datos.mes, DesafioMensual.anio == datos.anio)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un desafío para ese mes")
    d = DesafioMensual(**datos.model_dump())
    db.add(d)
    await db.commit()
    await db.refresh(d, ["ganador"])
    gestor.notificar_en_segundo_plano(tareas, Eventos.DESAFIO_PUBLICADO, {"desafio_id": d.id, "titulo": d.titulo},
                                      actor_id=admin.id)
    return await desafio_out(db, d)


@router.post("/desafios/{desafio_id}/ganador", response_model=DesafioOut, summary="Elegir la participación ganadora")
async def elegir_ganador(desafio_id: uuid.UUID, datos: GanadorIn, admin: Admin, db: DbSession, gestor: Gestor,
                         tareas: BackgroundTasks):
    d = await db.get(DesafioMensual, desafio_id)
    p = await db.get(ParticipacionDesafio, datos.participacion_id)
    if d is None or p is None or p.desafio_id != d.id or p.oculto:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Participación no encontrada en este desafío")
    d.ganador_id = p.usuario_id
    await db.commit()
    await db.refresh(d, ["ganador"])
    gestor.notificar_en_segundo_plano(tareas, Eventos.DESAFIO_GANADOR,
                                      {"desafio_id": d.id, "titulo": d.titulo, "ganador_id": p.usuario_id},
                                      actor_id=admin.id)
    return await desafio_out(db, d)


# ---------------------------------------------------------------- Bitácora (RegistroAuditoriaObserver)
@router.get("/auditoria", response_model=list[AuditoriaOut], summary="Últimos eventos registrados por el Observer")
async def auditoria(admin: Admin, db: DbSession, limite: Annotated[int, Query(ge=1, le=200)] = 50):
    filas = (await db.execute(
        select(RegistroAuditoria, Usuario).outerjoin(Usuario, Usuario.id == RegistroAuditoria.actor_id)
        .order_by(RegistroAuditoria.created_at.desc()).limit(limite)
    )).unique().all()
    return [AuditoriaOut(id=a.id, evento=a.evento, actor=AutorResumen.de(u), detalle=a.detalle, created_at=a.created_at)
            for a, u in filas]
