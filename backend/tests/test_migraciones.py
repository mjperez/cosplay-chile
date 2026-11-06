"""Criterio de aceptación: `alembic upgrade head` sobre una base vacía."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

RAIZ = Path(__file__).resolve().parents[1]

TABLAS_ESPERADAS = {
    "usuario",
    "perfil_cosplayer",
    "categoria_contenido",
    "contenido",
    "guia_tutorial",
    "entrevista",
    "articulo",
    "evento_cosplay",
    "participacion_evento",
    "proveedor",
    "donde_comprar",
    "comunidad_grupo",
    "foro_tema",
    "foro_respuesta",
    "desafio_mensual",
}


def configurar(url: str) -> Config:
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.fixture
def url_sqlite(tmp_path: Path) -> str:
    return f"sqlite+pysqlite:///{(tmp_path / 'esquema.db').as_posix()}"


def test_upgrade_head_crea_todas_las_tablas(url_sqlite: str):
    command.upgrade(configurar(url_sqlite), "head")

    motor = sa.create_engine(url_sqlite)
    try:
        tablas = set(sa.inspect(motor).get_table_names())
    finally:
        motor.dispose()

    faltantes = TABLAS_ESPERADAS - tablas
    assert not faltantes, f"faltan tablas: {sorted(faltantes)}"
    assert "alembic_version" in tablas


def test_downgrade_deja_la_base_vacia(url_sqlite: str):
    cfg = configurar(url_sqlite)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    motor = sa.create_engine(url_sqlite)
    try:
        tablas = set(sa.inspect(motor).get_table_names())
    finally:
        motor.dispose()

    assert tablas <= {"alembic_version"}


def test_las_claves_foraneas_apuntan_a_tablas_existentes(url_sqlite: str):
    command.upgrade(configurar(url_sqlite), "head")

    motor = sa.create_engine(url_sqlite)
    try:
        inspector = sa.inspect(motor)
        tablas = set(inspector.get_table_names())
        for tabla in TABLAS_ESPERADAS:
            for fk in inspector.get_foreign_keys(tabla):
                assert fk["referred_table"] in tablas
    finally:
        motor.dispose()
