"""Los tres observadores comprometidos en el informe ES2.

Cada uno implementa `actualizar()` y escribe en la **misma transacción** de la
petición cuando el servicio le pasa la sesión. Si se les llama sin sesión (un
script, un worker o una prueba unitaria), abren una propia a través del
Singleton `DatabaseSessionManager`, que es el patrón 1 del mismo informe.

* `NotificacionInternaObserver` → avisos internos al usuario (RF-37).
* `CorreoModeradorObserver`     → bandeja de salida hacia moderación.
* `RegistroAuditoriaObserver`  → bitácora inmutable (Ley 19.223 / ISO 27002
  A.8.15), que es además el log de auditoría que pide la guía del prototipo.

Adaptación documentada: el ES2 proponía notificar «en segundo plano». Las
pruebas de integración mostraron que `BackgroundTasks` corre antes de que se
cierre `get_db`, y una segunda conexión sobre SQLite falla con
`database is locked`. Ejecutar los observadores dentro de la transacción evita
ese bloqueo y garantiza que un commit fallido no deje avisos huérfanos. El
único efecto diferido de verdad es el correo, que se encola en la bandeja de
salida en lugar de enviarse durante la petición.
"""

from __future__ import annotations

import uuid
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session_manager
from app.events.gestor import EventoDominio, Observador, TIPOS_MODERACION
from app.models.notificacion import BitacoraAuditoria, Notificacion
from app.models.usuario import Usuario

CORREO_MODERACION = "moderacion@cosplay.cl"

_PLANTILLAS: dict[str, tuple[str, str]] = {
    "contenido_enviado_revision": (
        "Contenido enviado a revisión",
        "«{titulo}» quedó pendiente de revisión. El equipo de moderación lo evaluará.",
    ),
    "contenido_publicado": (
        "Contenido publicado",
        "«{titulo}» ya está publicado y visible para toda la comunidad.",
    ),
    "evento_creado": (
        "Nuevo evento en el calendario",
        "Se agregó «{titulo}» al calendario de eventos cosplay.",
    ),
    "desafio_creado": (
        "Nuevo desafío mensual",
        "Se lanzó el desafío «{titulo}». ¡Anímate a participar!",
    ),
}

_TIPOS_A_TODA_LA_COMUNIDAD = frozenset({"evento_creado", "desafio_creado"})


def _texto(evento: EventoDominio) -> tuple[str, str]:
    titulo, cuerpo = _PLANTILLAS[evento.tipo]
    nombre = str(evento.detalle.get("titulo") or "la publicación")
    return titulo, cuerpo.format(titulo=nombre)


def _json_seguro(detalle: dict) -> dict:
    """El evento viaja a `sa.JSON`; los UUID se convierten a texto."""
    return {
        clave: str(valor) if isinstance(valor, uuid.UUID) else valor
        for clave, valor in detalle.items()
    }


def _con_sesion(
    sesion: Session | None, escribir: Callable[[Session], None]
) -> None:
    if sesion is not None:
        escribir(sesion)
    else:
        with get_session_manager().session() as propia:
            escribir(propia)


def _administradores(sesion: Session) -> list[uuid.UUID]:
    return list(
        sesion.scalars(
            select(Usuario.id_usuario).where(
                Usuario.activo.is_(True), Usuario.rol == "administrador"
            )
        ).all()
    )


def _activos(sesion: Session) -> list[uuid.UUID]:
    return list(
        sesion.scalars(select(Usuario.id_usuario).where(Usuario.activo.is_(True))).all()
    )


class NotificacionInternaObserver(Observador):
    """Genera avisos internos para los destinatarios que correspondan."""

    def actualizar(
        self, evento: EventoDominio, sesion: Session | None = None
    ) -> None:
        titulo, mensaje = _texto(evento)
        autor = evento.detalle.get("id_autor")

        def escribir(s: Session) -> None:
            if evento.tipo in _TIPOS_A_TODA_LA_COMUNIDAD:
                destinatarios = _activos(s)
                # Un aviso masivo no vuelve a quien lo originó: el admin que
                # publicó el evento ya sabe que lo publicó.
                excluidos = {evento.id_actor} if evento.id_actor is not None else set()
            else:
                # El autor recibe confirmación; moderación, la tarea pendiente.
                destinatarios = _administradores(s)
                if autor is not None:
                    destinatarios.append(uuid.UUID(str(autor)))
                excluidos = set()

            vistos: set[uuid.UUID] = set()
            for id_usuario in destinatarios:
                if id_usuario in excluidos or id_usuario in vistos:
                    continue
                vistos.add(id_usuario)
                s.add(
                    Notificacion(
                        id_usuario=id_usuario,
                        tipo=evento.tipo,
                        titulo=titulo,
                        mensaje=mensaje,
                        id_recurso=evento.id_recurso,
                    )
                )

        _con_sesion(sesion, escribir)


class CorreoModeradorObserver(Observador):
    """Deja constancia del correo que debe recibir el equipo de moderación."""

    def actualizar(
        self, evento: EventoDominio, sesion: Session | None = None
    ) -> None:
        if evento.tipo not in TIPOS_MODERACION:
            return
        titulo, mensaje = _texto(evento)

        def escribir(s: Session) -> None:
            s.add(
                BitacoraAuditoria(
                    categoria="correo_moderacion",
                    tipo_evento=evento.tipo,
                    id_actor=evento.id_actor,
                    id_recurso=evento.id_recurso,
                    detalle={
                        "destinatario": CORREO_MODERACION,
                        "asunto": f"[Cosplay Chile] {titulo}",
                        "cuerpo": mensaje,
                        "estado": "pendiente_de_envio",
                    },
                    ocurrido_en=evento.ocurrido_en,
                )
            )

        _con_sesion(sesion, escribir)


class RegistroAuditoriaObserver(Observador):
    """Bitácora de eventos de dominio: quién, qué, cuándo y sobre qué recurso."""

    def actualizar(
        self, evento: EventoDominio, sesion: Session | None = None
    ) -> None:
        def escribir(s: Session) -> None:
            actor = s.get(Usuario, evento.id_actor) if evento.id_actor is not None else None
            s.add(
                BitacoraAuditoria(
                    categoria="evento_dominio",
                    tipo_evento=evento.tipo,
                    id_actor=evento.id_actor,
                    correo_actor=actor.correo if actor is not None else None,
                    id_recurso=evento.id_recurso,
                    detalle=_json_seguro(evento.detalle),
                    ocurrido_en=evento.ocurrido_en,
                )
            )

        _con_sesion(sesion, escribir)
