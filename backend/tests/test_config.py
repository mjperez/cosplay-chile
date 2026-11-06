"""Criterio de aceptación: toda la configuración viene de variables de entorno."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings

BASE = {
    "database_url": "postgresql://usuario:clave@localhost:5432/cosplay",
    "jwt_secret": "x" * 32,
}


def crear(**sobrescrituras) -> Settings:
    parametros = {**BASE, **sobrescrituras}
    return Settings(**parametros)


def test_normaliza_el_esquema_postgresql():
    assert crear().database_url == "postgresql+psycopg://usuario:clave@localhost:5432/cosplay"


def test_normaliza_el_esquema_antiguo_postgres():
    ajustes = crear(database_url="postgres://usuario:clave@host/neondb")
    assert ajustes.database_url == "postgresql+psycopg://usuario:clave@host/neondb"


def test_respeta_un_driver_explicito():
    ajustes = crear(database_url="postgresql+psycopg2://usuario:clave@host/db")
    assert ajustes.database_url == "postgresql+psycopg2://usuario:clave@host/db"


def test_jwt_secret_es_obligatorio(monkeypatch):
    """Sin la variable y sin .env, la aplicación no debe arrancar.

    `_env_file=None` aísla la prueba del .env real del proyecto: si no, el
    archivo aportaría el secreto y la prueba pasaría por el motivo equivocado.
    """
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="sqlite:///archivo.db")


def test_jwt_secret_demasiado_corto_se_rechaza():
    with pytest.raises(ValidationError):
        crear(jwt_secret="corto")


def test_lee_el_entorno_del_proceso():
    assert get_settings().environment == "test"


def test_es_produccion_reconoce_el_valor():
    assert crear(environment="production").es_produccion is True
    assert crear(environment="local").es_produccion is False


def test_cors_acepta_lista_separada_por_comas():
    """El formato que suele quedar al copiar una URL desde el navegador."""
    ajustes = crear(cors_origins="http://localhost:5173,https://cosplay.cl")
    assert ajustes.cors_origins == ["http://localhost:5173", "https://cosplay.cl"]


def test_cors_acepta_un_solo_origen_sin_corchetes():
    assert crear(cors_origins="http://localhost:5173").cors_origins == [
        "http://localhost:5173"
    ]


def test_cors_acepta_json():
    assert crear(cors_origins='["https://a.cl","https://b.cl"]').cors_origins == [
        "https://a.cl",
        "https://b.cl",
    ]


def test_la_normalizacion_del_dsn_es_reutilizable():
    """Alembic usa la misma función para no duplicar la regla."""
    from app.core.config import normalizar_dsn

    assert normalizar_dsn("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
