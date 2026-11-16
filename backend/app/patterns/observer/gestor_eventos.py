"""Patrón Observer (informe, pág. 30; Fig. 13 y Fig. 15).

``GestorEventos`` es el sujeto observable. Los servicios de negocio llaman a
``notificar(nombre, datos)`` y no conocen a quién se avisa. Cada observer
implementa ``actualizar()``. Los observers se ejecutan en paralelo (el
Fork/Join de la Fig. 15) y en segundo plano, después de responder al usuario,
mediante ``BackgroundTasks`` de FastAPI. Un observer que falla no afecta a los
demás ni a la respuesta HTTP.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import BackgroundTasks

logger = logging.getLogger("cosplaychile.observer")


class Eventos:
    """Catálogo de eventos de dominio que publica el sistema."""
    USUARIO_REGISTRADO = "USUARIO_REGISTRADO"
    RECUPERACION_SOLICITADA = "RECUPERACION_SOLICITADA"
    CONTRASENA_RESTABLECIDA = "CONTRASENA_RESTABLECIDA"
    CUENTA_ELIMINADA = "CUENTA_ELIMINADA"
    NUEVO_TUTORIAL = "NUEVO_TUTORIAL"
    CONTENIDO_PUBLICADO = "CONTENIDO_PUBLICADO"
    CONTENIDO_RECHAZADO = "CONTENIDO_RECHAZADO"
    EVENTO_SUGERIDO = "EVENTO_SUGERIDO"
    EVENTO_PUBLICADO = "EVENTO_PUBLICADO"
    EVENTO_RECHAZADO = "EVENTO_RECHAZADO"
    DESAFIO_PUBLICADO = "DESAFIO_PUBLICADO"
    DESAFIO_GANADOR = "DESAFIO_GANADOR"
    NUEVA_RESPUESTA = "NUEVA_RESPUESTA"
    NUEVO_REPORTE = "NUEVO_REPORTE"
    REPORTE_RESUELTO = "REPORTE_RESUELTO"
    USUARIO_SUSPENDIDO = "USUARIO_SUSPENDIDO"
    USUARIO_REACTIVADO = "USUARIO_REACTIVADO"
    CONTACTO_RECIBIDO = "CONTACTO_RECIBIDO"


@dataclass(frozen=True)
class EventoDominio:
    nombre: str
    datos: dict[str, Any]
    actor_id: uuid.UUID | None = None
    ocurrido_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Observer(ABC):
    """Interfaz común de los suscriptores."""

    @abstractmethod
    async def actualizar(self, evento: EventoDominio) -> None: ...


class GestorEventos:
    """Sujeto observable."""

    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def suscribir(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def desuscribir(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    @property
    def observers(self) -> tuple[Observer, ...]:
        return tuple(self._observers)

    async def notificar(self, nombre: str, datos: dict[str, Any], actor_id: uuid.UUID | None = None) -> None:
        """Avisa a todos los observers en paralelo; aísla los errores de cada uno."""
        evento = EventoDominio(nombre=nombre, datos=datos, actor_id=actor_id)
        resultados = await asyncio.gather(
            *(obs.actualizar(evento) for obs in self._observers), return_exceptions=True
        )
        for obs, res in zip(self._observers, resultados):
            if isinstance(res, BaseException):
                logger.error("Observer %s falló con %s: %r", type(obs).__name__, nombre, res)

    def notificar_en_segundo_plano(
        self,
        tareas: BackgroundTasks,
        nombre: str,
        datos: dict[str, Any],
        actor_id: uuid.UUID | None = None,
    ) -> None:
        """Agenda la notificación para después de enviar la respuesta HTTP."""
        tareas.add_task(self.notificar, nombre, datos, actor_id)
