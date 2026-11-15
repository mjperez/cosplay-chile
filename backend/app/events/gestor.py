"""Sujeto observable del patrón Observer (ES2, sección 3).

El informe comprometió un `GestorEventos` con tres observadores que implementan
`actualizar()` y se ejecutan en segundo plano. Este módulo es ese sujeto:

* `EventoDominio` es el mensaje, y solo contiene tipos primitivos. Así se puede
  encolar en un `BackgroundTasks` sin arrastrar objetos ORM de una sesión que
  ya se cerró.
* `GestorEventos.notificar()` recorre los suscriptores y **aísla sus fallos**:
  que un canal de aviso esté caído no puede convertir un `POST /contenido`
  correcto en un 500. Es la contrapartida real de «bajo acoplamiento».
* Los observadores reciben la **misma sesión** de la petición y escriben en la
  misma transacción. El informe ES2 proponía hacerlo en segundo plano; las
  pruebas de integración detectaron que `BackgroundTasks` se ejecuta antes de
  que se cierre la dependencia `get_db`, y una segunda conexión sobre SQLite
  falla con `database is locked`. Dentro de la transacción, además, un commit
  fallido no deja notificaciones huérfanas. El único efecto realmente diferido
  es el correo a moderación, que queda en bandeja de salida.

Los servicios no importan FastAPI: solo emiten un `EventoDominio`, así las
reglas de negocio siguen siendo testeables sin levantar HTTP.
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

registro = logging.getLogger("cosplay.eventos")

# Catálogo cerrado: agregar un tipo aquí obliga a decidir a quién se notifica.
TIPOS_EVENTO: dict[str, str] = {
    "contenido_enviado_revision": "Un tutorial fue enviado a revisión",
    "contenido_publicado": "Un contenido fue publicado",
    "evento_creado": "Se publicó un evento en el calendario",
    "desafio_creado": "Se lanzó un desafío mensual",
}

TIPOS_MODERACION = frozenset({"contenido_enviado_revision"})


@dataclass(frozen=True, slots=True)
class EventoDominio:
    """Mensaje inmutable que viaja del emisor a los observadores."""

    tipo: str
    detalle: dict[str, Any] = field(default_factory=dict)
    id_actor: uuid.UUID | None = None
    id_recurso: uuid.UUID | None = None
    ocurrido_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_EVENTO:
            raise ValueError(f"tipo de evento no registrado: {self.tipo}")


class Observador(ABC):
    """Interfaz común exigida por el informe: método `actualizar()`."""

    @abstractmethod
    def actualizar(
        self, evento: EventoDominio, sesion: Session | None = None
    ) -> None:
        """Reacciona al evento.

        Con `sesion` usa la transacción de la petición. Sin ella (llamadas
        directas, scripts o workers) abre una sesión propia.
        """


class GestorEventos:
    """Sujeto observable. Mantiene la lista de suscriptores."""

    def __init__(self) -> None:
        self._observadores: list[Observador] = []

    def suscribir(self, observador: Observador) -> None:
        if not any(type(previo) is type(observador) for previo in self._observadores):
            self._observadores.append(observador)

    def desuscribir(self, observador: Observador) -> None:
        self._observadores = [
            previo for previo in self._observadores if type(previo) is not type(observador)
        ]

    def limpiar(self) -> None:
        self._observadores.clear()

    def observadores(self) -> tuple[Observador, ...]:
        return tuple(self._observadores)

    def notificar(
        self, evento: EventoDominio, sesion: Session | None = None
    ) -> None:
        for observador in self.observadores():
            try:
                observador.actualizar(evento, sesion)
            except Exception:  # noqa: BLE001 - un canal caído no tumba la petición
                registro.exception(
                    "observador %s falló al procesar %s",
                    type(observador).__name__,
                    evento.tipo,
                )


gestor_eventos = GestorEventos()


def configurar_observadores() -> GestorEventos:
    """Registra los tres observadores del informe. Idempotente.

    Se llama una vez en el `lifespan` de la app. Limpiar antes de suscribir
    evita duplicados cuando los tests crean varios `TestClient`.
    """
    from app.events.observadores import (
        CorreoModeradorObserver,
        NotificacionInternaObserver,
        RegistroAuditoriaObserver,
    )

    gestor_eventos.limpiar()
    for observador in (
        NotificacionInternaObserver(),
        CorreoModeradorObserver(),
        RegistroAuditoriaObserver(),
    ):
        gestor_eventos.suscribir(observador)
    return gestor_eventos


Publicador = Callable[[EventoDominio], None]


def emitir(
    evento: EventoDominio,
    sesion: Session | None = None,
    publicador: Publicador | None = None,
) -> None:
    """Punto único de emisión usado por los servicios de dominio.

    `publicador` existe para las pruebas y para futuros workers: permite
    sustituir el despacho sin tocar las reglas de negocio.
    """
    if publicador is not None:
        publicador(evento)
    else:
        gestor_eventos.notificar(evento, sesion)
