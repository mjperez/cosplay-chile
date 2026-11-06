"""Configuración común de las pruebas.

Las variables de entorno se fijan antes de importar la aplicación: `Settings`
las lee al construirse y el Singleton las usa para crear el motor.

Las pruebas corren sobre SQLite en un directorio temporal, con el esquema
aplicado por la misma migración de Alembic que se usa en producción. Así se
verifica el esquema real y no una copia hecha con `create_all`.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

_DIR_TEMPORAL = Path(tempfile.mkdtemp(prefix="cosplay-test-"))
_RUTA_BD = _DIR_TEMPORAL / "pruebas.db"

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_RUTA_BD.as_posix()}"
os.environ["JWT_SECRET"] = "clave-de-prueba-con-mas-de-16-caracteres"
os.environ["ENVIRONMENT"] = "test"
os.environ["DB_ECHO"] = "false"
# bcrypt con costo 12 tarda unos 250 ms por hash. En pruebas no aporta nada.
os.environ["BCRYPT_ROUNDS"] = "4"

# Orden inverso de dependencias para poder borrar sin violar claves foráneas.
TABLAS = [
    "foro_respuesta",
    "foro_tema",
    "desafio_mensual",
    "participacion_evento",
    "guia_tutorial",
    "entrevista",
    "articulo",
    "contenido",
    "categoria_contenido",
    "perfil_cosplayer",
    "evento_cosplay",
    "proveedor",
    "donde_comprar",
    "comunidad_grupo",
    "intento_login",
    "usuario",
]


@pytest.fixture(scope="session", autouse=True)
def esquema_aplicado():
    """Aplica todas las migraciones una vez por sesión de pruebas."""
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "migrations"))
    cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def base_limpia(esquema_aplicado):
    """Vacía las tablas antes de cada prueba."""
    import sqlalchemy as sa

    motor = sa.create_engine(os.environ["DATABASE_URL"])
    with motor.begin() as conexion:
        for tabla in TABLAS:
            conexion.execute(sa.text(f"DELETE FROM {tabla}"))
    motor.dispose()
    yield


@pytest.fixture(autouse=True)
def infraestructura_limpia():
    """Descarta el motor y la configuración entre pruebas."""
    from app.core.config import get_settings
    from app.core.database import DatabaseSessionManager

    get_settings.cache_clear()
    DatabaseSessionManager.reset()
    yield
    DatabaseSessionManager.reset()
    get_settings.cache_clear()


@pytest.fixture
def cliente():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def datos_registro():
    """Cuerpo válido de registro. Cada prueba lo modifica si lo necesita."""
    from app.core.privacidad import VERSION

    return {
        "nombre": "Camila Rojas",
        "correo": "camila@ejemplo.cl",
        "password": "Cosplay2026!",
        "rol": "cosplayer",
        "region": "Valparaíso",
        "acepta_privacidad": True,
        "consentimiento_version": VERSION,
    }


@pytest.fixture
def crear_usuario(cliente, datos_registro):
    """Registra un usuario y devuelve (respuesta, cuerpo enviado)."""

    def _crear(**sobrescrituras):
        cuerpo = {**datos_registro, **sobrescrituras}
        respuesta = cliente.post("/api/v1/auth/registro", json=cuerpo)
        return respuesta, cuerpo

    return _crear
