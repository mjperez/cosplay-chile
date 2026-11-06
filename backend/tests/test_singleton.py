"""Criterio de aceptación: dos llamadas al gestor devuelven el mismo objeto."""

from __future__ import annotations

from app.core.database import DatabaseSessionManager, get_session_manager


def test_dos_llamadas_devuelven_el_mismo_objeto():
    primero = DatabaseSessionManager()
    segundo = DatabaseSessionManager()

    assert primero is segundo
    assert id(primero) == id(segundo)


def test_dependencia_de_fastapi_devuelve_la_misma_instancia():
    assert get_session_manager() is get_session_manager()
    assert get_session_manager() is DatabaseSessionManager()


def test_el_motor_se_construye_una_sola_vez():
    assert DatabaseSessionManager().engine is DatabaseSessionManager().engine


def test_reset_permite_construir_una_instancia_nueva():
    original = DatabaseSessionManager()
    DatabaseSessionManager.reset()
    reconstruida = DatabaseSessionManager()

    assert reconstruida is not original
    assert id(reconstruida) != id(original)
