"""Criterio de aceptación: autorización por rol y vigencia del token."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import update

from app.core.config import get_settings
from app.core.database import get_session_manager
from app.models.usuario import Usuario

ADMIN = "/api/v1/admin/usuarios"
YO = "/api/v1/auth/me"


def _token(cliente, correo: str, password: str) -> str:
    respuesta = cliente.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


def _cabecera(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _promover_a_admin(correo: str) -> None:
    with get_session_manager().session() as sesion:
        sesion.execute(update(Usuario).where(Usuario.correo == correo).values(rol="administrador"))


def test_me_sin_token_devuelve_401(cliente):
    respuesta = cliente.get(YO)

    assert respuesta.status_code == 401
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"


def test_me_con_token_valido_devuelve_el_usuario(cliente, crear_usuario):
    _, cuerpo = crear_usuario()
    token = _token(cliente, cuerpo["correo"], cuerpo["password"])

    respuesta = cliente.get(YO, headers=_cabecera(token))

    assert respuesta.status_code == 200
    assert respuesta.json()["correo"] == cuerpo["correo"]


def test_el_token_sirve_en_varias_peticiones(cliente, crear_usuario):
    """La sesión es stateless: el mismo token vale hasta que vence.

    Es lo que permite que el frontend la conserve en localStorage y el usuario
    siga dentro después de recargar la página.
    """
    _, cuerpo = crear_usuario()
    token = _token(cliente, cuerpo["correo"], cuerpo["password"])

    for _ in range(3):
        assert cliente.get(YO, headers=_cabecera(token)).status_code == 200


def test_token_vencido_devuelve_401(cliente, crear_usuario):
    _, cuerpo = crear_usuario()
    ajustes = get_settings()
    vencido = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "rol": "cosplayer",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        ajustes.jwt_secret,
        algorithm=ajustes.jwt_algorithm,
    )

    respuesta = cliente.get(YO, headers=_cabecera(vencido))

    assert respuesta.status_code == 401
    assert "expir" in respuesta.json()["detail"]


def test_token_malformado_devuelve_401(cliente):
    respuesta = cliente.get(YO, headers=_cabecera("esto.no.es.un.jwt"))

    assert respuesta.status_code == 401


def test_admin_sin_token_devuelve_401(cliente):
    assert cliente.get(ADMIN).status_code == 401


def test_usuario_normal_recibe_403_en_endpoints_de_administracion(cliente, crear_usuario):
    _, cuerpo = crear_usuario(rol="cosplayer")
    token = _token(cliente, cuerpo["correo"], cuerpo["password"])

    respuesta = cliente.get(ADMIN, headers=_cabecera(token))

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "no tienes permisos para esta operación"


def test_administrador_entra_a_los_endpoints_de_administracion(cliente, crear_usuario):
    _, cuerpo = crear_usuario(rol="cosplayer")
    _promover_a_admin(cuerpo["correo"])
    token = _token(cliente, cuerpo["correo"], cuerpo["password"])

    respuesta = cliente.get(ADMIN, headers=_cabecera(token))

    assert respuesta.status_code == 200
    cuerpo_respuesta = respuesta.json()
    assert cuerpo_respuesta["total"] == 1
    assert cuerpo_respuesta["elementos"][0]["rol"] == "administrador"


def test_el_rol_se_lee_de_la_base_no_del_token(cliente, crear_usuario):
    """Revocar un rol surte efecto sin esperar a que venza el token."""
    _, cuerpo = crear_usuario(rol="cosplayer")
    _promover_a_admin(cuerpo["correo"])
    token = _token(cliente, cuerpo["correo"], cuerpo["password"])
    assert cliente.get(ADMIN, headers=_cabecera(token)).status_code == 200

    with get_session_manager().session() as sesion:
        sesion.execute(
            update(Usuario).where(Usuario.correo == cuerpo["correo"]).values(rol="cosplayer")
        )

    assert cliente.get(ADMIN, headers=_cabecera(token)).status_code == 403
