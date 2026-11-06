"""Criterios de aceptación del login: 401 sin filtrar y bloqueo por intentos."""

from __future__ import annotations

from sqlalchemy import func, select, update

from app.core.database import get_session_manager
from app.models.intento_login import IntentoLogin
from app.models.usuario import Usuario

LOGIN = "/api/v1/auth/login"


def _cambiar_activo(correo: str, activo: bool) -> None:
    with get_session_manager().session() as sesion:
        sesion.execute(update(Usuario).where(Usuario.correo == correo).values(activo=activo))


def test_login_correcto_devuelve_token(cliente, crear_usuario):
    respuesta, cuerpo = crear_usuario()
    assert respuesta.status_code == 201

    login = cliente.post(LOGIN, json={"correo": cuerpo["correo"], "password": cuerpo["password"]})

    assert login.status_code == 200
    datos = login.json()
    assert datos["token_type"] == "bearer"
    assert datos["expires_in"] > 0
    assert len(datos["access_token"].split(".")) == 3
    assert datos["usuario"]["correo"] == cuerpo["correo"]
    assert "password_hash" not in datos["usuario"]


def test_contrasena_incorrecta_devuelve_401(cliente, crear_usuario):
    _, cuerpo = crear_usuario()

    login = cliente.post(LOGIN, json={"correo": cuerpo["correo"], "password": "incorrecta"})

    assert login.status_code == 401


def test_correo_inexistente_responde_igual_que_contrasena_incorrecta(cliente, crear_usuario):
    """Si los mensajes difirieran, se podría enumerar qué correos existen."""
    _, cuerpo = crear_usuario()

    con_clave_mala = cliente.post(
        LOGIN, json={"correo": cuerpo["correo"], "password": "incorrecta"}
    )
    sin_cuenta = cliente.post(
        LOGIN, json={"correo": "nadie@ejemplo.cl", "password": "incorrecta"}
    )

    assert con_clave_mala.status_code == sin_cuenta.status_code == 401
    assert con_clave_mala.json()["detail"] == sin_cuenta.json()["detail"]


def test_cuenta_deshabilitada_responde_igual_que_credenciales_invalidas(cliente, crear_usuario):
    _, cuerpo = crear_usuario()
    _cambiar_activo(cuerpo["correo"], False)

    login = cliente.post(LOGIN, json={"correo": cuerpo["correo"], "password": cuerpo["password"]})

    assert login.status_code == 401
    assert login.json()["detail"] == "correo o contraseña incorrectos"


def test_cinco_fallos_bloquean_el_login(cliente, crear_usuario):
    _, cuerpo = crear_usuario()
    credenciales = {"correo": cuerpo["correo"], "password": "incorrecta"}

    for intento in range(5):
        respuesta = cliente.post(LOGIN, json=credenciales)
        assert respuesta.status_code == 401, f"el intento {intento + 1} debía dar 401"

    bloqueado = cliente.post(LOGIN, json=credenciales)

    assert bloqueado.status_code == 429
    assert int(bloqueado.headers["Retry-After"]) > 0


def test_el_bloqueo_tambien_aplica_con_la_contrasena_correcta(cliente, crear_usuario):
    """El bloqueo no se salta acertando la clave: si no, no serviría de nada."""
    _, cuerpo = crear_usuario()

    for _ in range(5):
        cliente.post(LOGIN, json={"correo": cuerpo["correo"], "password": "incorrecta"})

    respuesta = cliente.post(
        LOGIN, json={"correo": cuerpo["correo"], "password": cuerpo["password"]}
    )

    assert respuesta.status_code == 429


def test_el_bloqueo_aplica_aunque_la_cuenta_no_exista(cliente):
    """Si solo bloqueara cuentas reales, el 429 delataría cuáles existen."""
    credenciales = {"correo": "fantasma@ejemplo.cl", "password": "incorrecta"}

    for _ in range(5):
        assert cliente.post(LOGIN, json=credenciales).status_code == 401

    assert cliente.post(LOGIN, json=credenciales).status_code == 429


def test_un_login_exitoso_limpia_los_fallos_previos(cliente, crear_usuario):
    _, cuerpo = crear_usuario()

    for _ in range(4):
        cliente.post(LOGIN, json={"correo": cuerpo["correo"], "password": "incorrecta"})

    correcto = cliente.post(
        LOGIN, json={"correo": cuerpo["correo"], "password": cuerpo["password"]}
    )
    assert correcto.status_code == 200

    with get_session_manager().session() as sesion:
        fallidos = sesion.scalar(
            select(func.count())
            .select_from(IntentoLogin)
            .where(IntentoLogin.correo == cuerpo["correo"], IntentoLogin.exitoso.is_(False))
        )
    assert fallidos == 0
