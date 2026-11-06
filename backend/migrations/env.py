"""Entorno de ejecución de Alembic.

La cadena de conexión se toma de `DATABASE_URL`, nunca de `alembic.ini`, para
que el mismo repositorio sirva en local, en CI y en Render sin secretos
versionados.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.core.config import normalizar_dsn  # noqa: E402
from app.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def obtener_url() -> str:
    """Resuelve el DSN sin exigir el resto de la configuración.

    Una migración solo necesita la cadena de conexión. Construir `Settings`
    completo obligaría a tener JWT_SECRET para correr Alembic, que no tiene
    nada que ver. El orden es: `-x url=...`, `sqlalchemy.url` del ini,
    variable de entorno y, por último, el archivo .env.
    """
    override = context.get_x_argument(as_dictionary=True).get("url")
    if override:
        return normalizar_dsn(override)

    configurada = config.get_main_option("sqlalchemy.url")
    if configurada:
        return normalizar_dsn(configurada)

    del_entorno = os.environ.get("DATABASE_URL")
    if del_entorno:
        return normalizar_dsn(del_entorno)

    from dotenv import dotenv_values

    for ruta in (Path(".env"), RAIZ / ".env"):
        if ruta.is_file():
            valor = dotenv_values(ruta).get("DATABASE_URL")
            if valor:
                return normalizar_dsn(valor)

    raise RuntimeError("falta DATABASE_URL: defínela en el entorno o en .env")


def run_migrations_offline() -> None:
    context.configure(
        url=obtener_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    seccion = config.get_section(config.config_ini_section, {})
    seccion["sqlalchemy.url"] = obtener_url()

    connectable = engine_from_config(
        seccion,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
