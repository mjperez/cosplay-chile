"""Criterios de aceptación del registro: hash y consentimiento."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import select

from app.core.database import get_session_manager
from app.core.privacidad import VERSION
from app.models.usuario import Usuario

RUTA = "/api/v1/auth/registro"


def _usuario_en_bd(correo: str) -> Usuario | None:
    with get_session_manager().session() as sesion:
        return sesion.scalar(select(Usuario).where(Usuario.correo == correo))


def test_registro_devuelve_201_y_no_expone_el_hash(cliente, datos_registro):
    respuesta = cliente.post(RUTA, json=datos_registro)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["correo"] == datos_registro["correo"]
    assert cuerpo["rol"] == "cosplayer"
    assert "password" not in cuerpo
    assert "password_hash" not in cuerpo


def test_la_contrasena_se_guarda_hasheada(cliente, datos_registro):
    cliente.post(RUTA, json=datos_registro)

    usuario = _usuario_en_bd(datos_registro["correo"])

    assert usuario is not None
    assert usuario.password_hash != datos_registro["password"]
    assert datos_registro["password"] not in usuario.password_hash
    assert usuario.password_hash.startswith("$2b$")


def test_el_consentimiento_queda_con_fecha_y_version(cliente, datos_registro):
    cliente.post(RUTA, json=datos_registro)

    usuario = _usuario_en_bd(datos_registro["correo"])

    assert usuario is not None
    assert usuario.consentimiento_fecha is not None
    assert usuario.consentimiento_version == VERSION


def test_correo_duplicado_devuelve_409(cliente, datos_registro):
    cliente.post(RUTA, json=datos_registro)
    respuesta = cliente.post(RUTA, json=datos_registro)

    assert respuesta.status_code == 409


def test_no_se_puede_registrar_sin_aceptar_la_politica(cliente, datos_registro):
    respuesta = cliente.post(RUTA, json={**datos_registro, "acepta_privacidad": False})

    assert respuesta.status_code == 422


def test_version_de_privacidad_desconocida_se_rechaza(cliente, datos_registro):
    respuesta = cliente.post(RUTA, json={**datos_registro, "consentimiento_version": "0.1"})

    assert respuesta.status_code == 422


def test_no_se_puede_autoasignar_el_rol_administrador(cliente, datos_registro):
    respuesta = cliente.post(RUTA, json={**datos_registro, "rol": "administrador"})

    assert respuesta.status_code == 422


def test_contrasena_corta_se_rechaza(cliente, datos_registro):
    respuesta = cliente.post(RUTA, json={**datos_registro, "password": "corta"})

    assert respuesta.status_code == 422


def test_correo_mal_formado_se_rechaza(cliente, datos_registro):
    respuesta = cliente.post(RUTA, json={**datos_registro, "correo": "no-es-un-correo"})

    assert respuesta.status_code == 422


def test_la_politica_expone_la_version_vigente(cliente):
    respuesta = cliente.get("/api/v1/privacidad")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["version"] == VERSION
    assert "Ley 21.719" in cuerpo["texto"]


def test_el_esquema_no_tiene_columnas_de_texto_plano(cliente, datos_registro):
    """Comprobación directa sobre la base: no existe una columna con la clave."""
    cliente.post(RUTA, json=datos_registro)

    motor = sa.create_engine("sqlite:///" + str(get_session_manager().engine.url.database))
    try:
        columnas = {c["name"] for c in sa.inspect(motor).get_columns("usuario")}
    finally:
        motor.dispose()

    assert "password" not in columnas
    assert "password_hash" in columnas
