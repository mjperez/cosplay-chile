"""Criterio de aceptación: hash irreversible y tokens firmados."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import Settings
from app.core.security import (
    MAX_BYTES_PASSWORD,
    crear_token_acceso,
    decodificar_token,
    hash_password,
    verificar_password,
    verificar_senuelo,
)

AJUSTES = Settings(
    database_url="sqlite:///no-se-usa.db",
    jwt_secret="clave-de-prueba-con-mas-de-16-caracteres",
    bcrypt_rounds=4,
    jwt_expire_minutes=30,
)

PASSWORD = "Cosplay2026!"


def test_el_hash_no_contiene_la_contrasena():
    resultado = hash_password(PASSWORD, AJUSTES)
    assert PASSWORD not in resultado
    assert resultado.startswith("$2b$")


def test_el_mismo_password_produce_hashes_distintos():
    """La sal aleatoria impide comparar hashes entre usuarios."""
    assert hash_password(PASSWORD, AJUSTES) != hash_password(PASSWORD, AJUSTES)


def test_verificacion_correcta():
    assert verificar_password(PASSWORD, hash_password(PASSWORD, AJUSTES)) is True


def test_verificacion_incorrecta():
    assert verificar_password("otra-clave", hash_password(PASSWORD, AJUSTES)) is False


def test_hash_corrupto_cuenta_como_fallo():
    assert verificar_password(PASSWORD, "esto-no-es-un-hash") is False


def test_rechaza_contrasenas_de_mas_de_72_bytes():
    with pytest.raises(ValueError):
        hash_password("a" * (MAX_BYTES_PASSWORD + 1), AJUSTES)


def test_el_senuelo_no_revienta_con_entradas_raras():
    verificar_senuelo("")
    verificar_senuelo("a" * 200)


def test_token_lleva_sujeto_y_rol():
    id_usuario = uuid.uuid4()
    token, vigencia = crear_token_acceso(
        id_usuario=id_usuario, rol="cosplayer", settings=AJUSTES
    )

    payload = decodificar_token(token, AJUSTES)

    assert payload["sub"] == str(id_usuario)
    assert payload["rol"] == "cosplayer"
    assert vigencia == AJUSTES.jwt_expire_minutes * 60


def test_token_vencido_se_rechaza():
    payload = {
        "sub": str(uuid.uuid4()),
        "rol": "cosplayer",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=5),
    }
    token = jwt.encode(payload, AJUSTES.jwt_secret, algorithm="HS256")

    with pytest.raises(jwt.ExpiredSignatureError):
        decodificar_token(token, AJUSTES)


def test_token_firmado_con_otra_clave_se_rechaza():
    payload = {"sub": str(uuid.uuid4()), "rol": "cosplayer"}
    otra_clave = "clave-ajena-con-mas-de-treinta-y-dos-caracteres"
    token = jwt.encode(payload, otra_clave, algorithm="HS256")

    with pytest.raises(jwt.InvalidTokenError):
        decodificar_token(token, AJUSTES)
