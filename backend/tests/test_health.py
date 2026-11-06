"""Criterio de aceptación: GET /health responde con el estado de la base."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_responde_200_con_el_estado_de_la_base():
    with TestClient(app) as cliente:
        respuesta = cliente.get("/health")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "ok"
    assert cuerpo["database"]["ok"] is True
    assert cuerpo["database"]["latencia_ms"] >= 0
    assert "version" in cuerpo


def test_health_no_expone_la_cadena_de_conexion():
    with TestClient(app) as cliente:
        cuerpo = cliente.get("/health").json()

    texto = str(cuerpo)
    assert "password" not in texto
    assert "postgresql://" not in texto


def test_la_raiz_apunta_a_la_documentacion():
    with TestClient(app) as cliente:
        respuesta = cliente.get("/")

    assert respuesta.status_code == 200
    assert respuesta.json()["salud"] == "/health"
