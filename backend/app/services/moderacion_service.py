"""Gestionar Soporte y Reportes + Bloquear/Sancionar Usuario (Fig. 10, RF-38, RF-40)."""
from datetime import datetime, timezone
from enum import Enum

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunidad import ParticipacionDesafio, Respuesta, Tema
from app.models.contenido import Contenido
from app.models.directorio import DirectorioItem, Resena
from app.models.enums import EstadoPublicacion, EstadoReporte, EstadoUsuario, Rol, TipoObjetoReporte
from app.models.evento import Evento
from app.models.interaccion import Reporte
from app.models.usuario import Usuario
from app.patterns.observer import Eventos, GestorEventos

MODELOS = {
    TipoObjetoReporte.CONTENIDO: Contenido,
    TipoObjetoReporte.TEMA: Tema,
    TipoObjetoReporte.RESPUESTA: Respuesta,
    TipoObjetoReporte.EVENTO: Evento,
    TipoObjetoReporte.DIRECTORIO: DirectorioItem,
    TipoObjetoReporte.RESENA: Resena,
    TipoObjetoReporte.PARTICIPACION_DESAFIO: ParticipacionDesafio,
}


class AccionReporte(str, Enum):
    DESCARTAR = "DESCARTAR"            # el reporte no procede
    RESOLVER = "RESOLVER"              # se atendió sin sanción (p. ej. se corrigió el evento)
    OCULTAR = "OCULTAR"                # se retira el contenido
    OCULTAR_Y_SUSPENDER = "OCULTAR_Y_SUSPENDER"  # se retira y se suspende a quien lo publicó


def autor_de(tipo: TipoObjetoReporte, obj):
    return {
        TipoObjetoReporte.CONTENIDO: lambda o: o.autor_id,
        TipoObjetoReporte.TEMA: lambda o: o.autor_id,
        TipoObjetoReporte.RESPUESTA: lambda o: o.autor_id,
        TipoObjetoReporte.EVENTO: lambda o: o.creado_por_id,
        TipoObjetoReporte.DIRECTORIO: lambda o: o.usuario_id,
        TipoObjetoReporte.RESENA: lambda o: o.usuario_id,
        TipoObjetoReporte.PARTICIPACION_DESAFIO: lambda o: o.usuario_id,
    }[tipo](obj)


def resumen_objeto(tipo: TipoObjetoReporte, obj) -> dict:
    """Texto, enlace y estado del objeto reportado, para que moderación decida sin salir del panel."""
    if obj is None:
        return {"texto": "(el contenido ya no existe)", "enlace": None, "oculto": True}
    t = TipoObjetoReporte
    if tipo == t.CONTENIDO:
        return {"texto": obj.titulo, "enlace": f"/guias/{obj.id}", "oculto": obj.estado == EstadoPublicacion.OCULTO}
    if tipo == t.TEMA:
        return {"texto": f"{obj.titulo}: {obj.contenido[:200]}", "enlace": f"/comunidad/temas/{obj.id}", "oculto": obj.oculto}
    if tipo == t.RESPUESTA:
        return {"texto": obj.contenido[:300], "enlace": f"/comunidad/temas/{obj.tema_id}#respuesta-{obj.id}", "oculto": obj.oculto}
    if tipo == t.EVENTO:
        return {"texto": f"{obj.nombre} ({obj.fecha_inicio:%d-%m-%Y}, {obj.lugar})", "enlace": f"/calendario/{obj.id}",
                "oculto": obj.estado == EstadoPublicacion.OCULTO}
    if tipo == t.DIRECTORIO:
        return {"texto": obj.nombre, "enlace": f"/directorio/{obj.id}", "oculto": not obj.activo}
    if tipo == t.RESENA:
        return {"texto": f"{obj.calificacion}★ {obj.comentario[:250]}", "enlace": f"/directorio/{obj.directorio_item_id}",
                "oculto": obj.oculta}
    return {"texto": obj.titulo, "enlace": f"/desafios/{obj.desafio_id}", "oculto": obj.oculto}


def ocultar(tipo: TipoObjetoReporte, obj) -> None:
    t = TipoObjetoReporte
    if tipo in (t.CONTENIDO, t.EVENTO):
        obj.estado = EstadoPublicacion.OCULTO
    elif tipo == t.DIRECTORIO:
        obj.activo = False
    elif tipo == t.RESENA:
        obj.oculta = True
    else:
        obj.oculto = True


async def suspender(db: AsyncSession, admin: Usuario, usuario: Usuario, motivo: str) -> None:
    if usuario.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes suspender tu propia cuenta")
    if usuario.rol == Rol.ADMIN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se puede suspender a una cuenta de moderación")
    if usuario.estado == EstadoUsuario.ELIMINADO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La cuenta fue eliminada")
    usuario.estado = EstadoUsuario.SUSPENDIDO
    usuario.motivo_suspension = motivo


async def resolver_reporte(
    db: AsyncSession, gestor: GestorEventos, tareas: BackgroundTasks, admin: Usuario,
    reporte: Reporte, accion: AccionReporte, resolucion: str,
) -> Reporte:
    if reporte.estado != EstadoReporte.ABIERTO:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este reporte ya fue resuelto")
    obj = await db.get(MODELOS[reporte.tipo_objeto], reporte.objeto_id)
    suspendido_id = None
    if accion in (AccionReporte.OCULTAR, AccionReporte.OCULTAR_Y_SUSPENDER):
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El contenido reportado ya no existe")
        ocultar(reporte.tipo_objeto, obj)
    if accion == AccionReporte.OCULTAR_Y_SUSPENDER:
        autor_id = autor_de(reporte.tipo_objeto, obj)
        autor = await db.get(Usuario, autor_id) if autor_id else None
        if autor is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este contenido no tiene una cuenta asociada que suspender")
        await suspender(db, admin, autor, resolucion)
        suspendido_id = autor.id
    reporte.estado = EstadoReporte.DESCARTADO if accion == AccionReporte.DESCARTAR else EstadoReporte.RESUELTO
    reporte.resolucion = f"[{accion.value}] {resolucion}".strip()
    reporte.resuelto_por_id = admin.id
    reporte.resuelto_at = datetime.now(timezone.utc)
    await db.commit()
    gestor.notificar_en_segundo_plano(
        tareas, Eventos.REPORTE_RESUELTO,
        {"reporte_id": reporte.id, "accion": accion.value, "tipo_objeto": reporte.tipo_objeto},
        actor_id=admin.id,
    )
    if suspendido_id:
        gestor.notificar_en_segundo_plano(tareas, Eventos.USUARIO_SUSPENDIDO,
                                          {"usuario_id": suspendido_id, "motivo": resolucion}, actor_id=admin.id)
    return reporte
