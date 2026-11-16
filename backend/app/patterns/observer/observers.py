"""Observers concretos suscritos al GestorEventos.

Cada uno abre su propia sesión desde el Singleton DatabaseSessionManager porque
corre después de cerrada la petición original.
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import func, insert, literal, select

from app.core.config import get_settings
from app.db.session_manager import DatabaseSessionManager
from app.models.enums import EstadoUsuario, Rol
from app.models.interaccion import Notificacion, RegistroAuditoria
from app.models.usuario import Usuario
from app.patterns.observer.gestor_eventos import EventoDominio, Eventos, Observer
from app.services.correo import enviar_correo_simulado

logger = logging.getLogger("cosplaychile.observer")


def _uuid(valor) -> uuid.UUID | None:
    if valor is None:
        return None
    return valor if isinstance(valor, uuid.UUID) else uuid.UUID(str(valor))


def _json_seguro(valor):
    if isinstance(valor, dict):
        return {k: _json_seguro(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_seguro(v) for v in valor]
    if isinstance(valor, (uuid.UUID, datetime, date)):
        return str(valor)
    if isinstance(valor, Enum):
        return valor.value
    return valor


class NotificacionInternaObserver(Observer):
    """Genera notificaciones in-app (RF-37) para autores, moderación o toda la comunidad."""

    async def actualizar(self, evento: EventoDominio) -> None:
        d = evento.datos
        n = evento.nombre
        async with DatabaseSessionManager().session() as s:
            if n == Eventos.NUEVO_TUTORIAL:
                await self._a_usuario(s, d["autor_id"], n,
                                      f"Tu tutorial «{d['titulo']}» está en revisión.", "/perfil#mis-envios")
                await self._a_admins(s, n, f"Nuevo tutorial pendiente de revisión: «{d['titulo']}».",
                                     "/moderacion?tab=contenidos")
            elif n == Eventos.CONTENIDO_PUBLICADO:
                await self._a_usuario(s, d["autor_id"], n,
                                      f"¡Tu contenido «{d['titulo']}» fue publicado!", f"/guias/{d['contenido_id']}")
                await self._a_todos(s, n, f"Nueva guía publicada: «{d['titulo']}».",
                                    f"/guias/{d['contenido_id']}", excluir=d["autor_id"])
            elif n == Eventos.CONTENIDO_RECHAZADO:
                motivo = d.get("motivo") or "sin detalle"
                await self._a_usuario(s, d["autor_id"], n,
                                      f"Tu contenido «{d['titulo']}» no fue aprobado. Motivo: {motivo}",
                                      "/perfil#mis-envios")
            elif n == Eventos.EVENTO_SUGERIDO:
                await self._a_usuario(s, d["autor_id"], n,
                                      f"Recibimos tu sugerencia de evento «{d['nombre']}». La revisaremos pronto.",
                                      "/calendario")
                await self._a_admins(s, n, f"Evento sugerido por la comunidad: «{d['nombre']}».",
                                     "/moderacion?tab=eventos")
            elif n == Eventos.EVENTO_PUBLICADO:
                if d.get("autor_id"):
                    await self._a_usuario(s, d["autor_id"], n,
                                          f"Tu sugerencia «{d['nombre']}» ya está en el calendario.",
                                          f"/calendario/{d['evento_id']}")
                await self._a_todos(s, n, f"Nuevo evento en el calendario: «{d['nombre']}».",
                                    f"/calendario/{d['evento_id']}", excluir=d.get("autor_id"))
            elif n == Eventos.EVENTO_RECHAZADO and d.get("autor_id"):
                await self._a_usuario(s, d["autor_id"], n,
                                      f"Tu sugerencia «{d['nombre']}» no fue incorporada al calendario.",
                                      "/calendario")
            elif n == Eventos.DESAFIO_PUBLICADO:
                await self._a_todos(s, n, f"Nuevo desafío mensual: «{d['titulo']}». ¡Participa!",
                                    f"/desafios/{d['desafio_id']}")
            elif n == Eventos.DESAFIO_GANADOR:
                await self._a_usuario(s, d["ganador_id"], n,
                                      f"¡Ganaste el desafío «{d['titulo']}»! Felicitaciones.",
                                      f"/desafios/{d['desafio_id']}")
            elif n == Eventos.NUEVA_RESPUESTA:
                if str(d["autor_tema_id"]) != str(d["autor_respuesta_id"]):
                    await self._a_usuario(s, d["autor_tema_id"], n,
                                          f"Respondieron tu tema «{d['titulo']}».", f"/comunidad/temas/{d['tema_id']}")
            elif n == Eventos.NUEVO_REPORTE:
                await self._a_admins(s, n, "Hay un nuevo reporte de contenido por revisar.",
                                     "/moderacion?tab=reportes")
            elif n == Eventos.CONTACTO_RECIBIDO:
                await self._a_admins(s, n, f"Nuevo mensaje de contacto: «{d['asunto']}».",
                                     "/moderacion?tab=contactos")
            else:
                return
            await s.commit()

    @staticmethod
    async def _a_usuario(s, usuario_id, tipo: str, mensaje: str, enlace: str | None) -> None:
        s.add(Notificacion(usuario_id=_uuid(usuario_id), tipo=tipo, mensaje=mensaje[:400], enlace=enlace))

    @staticmethod
    async def _a_admins(s, tipo: str, mensaje: str, enlace: str | None) -> None:
        await NotificacionInternaObserver._insertar_masivo(
            s, tipo, mensaje, enlace, (Usuario.rol == Rol.ADMIN,)
        )

    @staticmethod
    async def _a_todos(s, tipo: str, mensaje: str, enlace: str | None, excluir=None) -> None:
        condiciones = [Usuario.id != _uuid(excluir)] if excluir else []
        await NotificacionInternaObserver._insertar_masivo(s, tipo, mensaje, enlace, tuple(condiciones))

    @staticmethod
    async def _insertar_masivo(s, tipo, mensaje, enlace, condiciones) -> None:
        """INSERT ... SELECT: una sola sentencia aunque haya miles de usuarios.

        id y created_at se generan en el servidor por fila (los defaults de Python
        se evaluarían una sola vez para toda la sentencia).
        """
        origen = select(
            func.gen_random_uuid(), func.now(), Usuario.id, literal(tipo), literal(mensaje[:400]),
            literal(enlace), literal(False),
        ).where(Usuario.estado == EstadoUsuario.ACTIVO, *condiciones)
        await s.execute(
            insert(Notificacion).from_select(
                ["id", "created_at", "usuario_id", "tipo", "mensaje", "enlace", "leida"], origen
            )
        )


class CorreoModeradorObserver(Observer):
    """Avisa por correo al equipo de moderación (simulado con log en el prototipo)."""

    EVENTOS = {
        Eventos.NUEVO_TUTORIAL: "Nuevo tutorial pendiente de revisión",
        Eventos.EVENTO_SUGERIDO: "Nuevo evento sugerido",
        Eventos.NUEVO_REPORTE: "Nuevo reporte de contenido",
        Eventos.CONTACTO_RECIBIDO: "Nuevo mensaje en el formulario de contacto",
    }

    async def actualizar(self, evento: EventoDominio) -> None:
        asunto = self.EVENTOS.get(evento.nombre)
        if not asunto:
            return
        detalle = "\n".join(f"  {k}: {v}" for k, v in _json_seguro(evento.datos).items())
        enviar_correo_simulado(
            get_settings().correo_moderacion,
            f"[Cosplay Chile] {asunto}",
            f"Evento {evento.nombre} ({evento.ocurrido_at:%d-%m-%Y %H:%M} UTC)\n{detalle}",
        )


class RegistroAuditoriaObserver(Observer):
    """Escribe cada evento de dominio en la bitácora del sistema."""

    async def actualizar(self, evento: EventoDominio) -> None:
        async with DatabaseSessionManager().session() as s:
            s.add(
                RegistroAuditoria(
                    evento=evento.nombre,
                    actor_id=_uuid(evento.actor_id),
                    detalle=_json_seguro(evento.datos),
                )
            )
            await s.commit()
