from app.patterns.observer.gestor_eventos import EventoDominio, Eventos, GestorEventos, Observer
from app.patterns.observer.observers import (
    CorreoModeradorObserver,
    NotificacionInternaObserver,
    RegistroAuditoriaObserver,
)

_gestor: GestorEventos | None = None


def crear_gestor_eventos() -> GestorEventos:
    gestor = GestorEventos()
    gestor.suscribir(NotificacionInternaObserver())
    gestor.suscribir(CorreoModeradorObserver())
    gestor.suscribir(RegistroAuditoriaObserver())
    return gestor


def get_gestor_eventos() -> GestorEventos:
    """Dependencia de FastAPI (las pruebas pueden reemplazarla)."""
    global _gestor
    if _gestor is None:
        _gestor = crear_gestor_eventos()
    return _gestor


__all__ = [
    "CorreoModeradorObserver", "EventoDominio", "Eventos", "GestorEventos", "NotificacionInternaObserver",
    "Observer", "RegistroAuditoriaObserver", "crear_gestor_eventos", "get_gestor_eventos",
]
