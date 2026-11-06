"""Gestor de sesiones de base de datos implementado como Singleton.

El requerimiento US-01 pide una única instancia del motor dentro del proceso:
dos llamadas al gestor deben devolver el mismo objeto (`id()` idéntico). Eso
se consigue sobreescribiendo `__new__`, que es el punto donde Python decide si
crea un objeto nuevo o reutiliza uno existente.

Por qué no basta con una variable de módulo: una variable global se puede
reasignar desde cualquier import, y dos módulos que importen en momentos
distintos podrían construir dos motores. El Singleton a nivel de clase no
depende de quién importe primero.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


class DatabaseSessionManager:
    """Contenedor único del motor y del sessionmaker."""

    _instance: DatabaseSessionManager | None = None
    _lock = threading.Lock()

    def __new__(cls, settings: Settings | None = None) -> DatabaseSessionManager:
        # Doble verificación: el primer chequeo evita tomar el lock en cada
        # llamada; el segundo evita que dos hilos construyan el motor a la vez.
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instancia = super().__new__(cls)
                    instancia._construir(settings or get_settings())
                    cls._instance = instancia
        return cls._instance

    def _construir(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = self._crear_engine(settings)
        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @staticmethod
    def _crear_engine(settings: Settings) -> Engine:
        opciones: dict = {
            "echo": settings.db_echo,
            "future": True,
            "pool_pre_ping": True,
        }
        # SQLite no acepta los parámetros de pool de PostgreSQL y los tests
        # corren sobre SQLite en memoria.
        if not settings.database_url.startswith("sqlite"):
            opciones.update(
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_timeout=settings.db_pool_timeout,
                pool_recycle=settings.db_pool_recycle,
            )
        return create_engine(settings.database_url, **opciones)

    # --- Acceso ---------------------------------------------------------
    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        return self._session_factory

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Entrega una sesión y garantiza commit o rollback."""
        sesion = self._session_factory()
        try:
            yield sesion
            sesion.commit()
        except Exception:
            sesion.rollback()
            raise
        finally:
            sesion.close()

    # --- Diagnóstico ----------------------------------------------------
    def health_check(self) -> dict:
        """Ejecuta una consulta trivial y reporta el estado de la conexión."""
        inicio = time.perf_counter()
        try:
            with self._engine.connect() as conexion:
                conexion.execute(text("SELECT 1"))
            latencia = round((time.perf_counter() - inicio) * 1000, 2)
            return {"ok": True, "detalle": "conexion establecida", "latencia_ms": latencia}
        except Exception as exc:  # noqa: BLE001 - el health debe reportar, no lanzar
            latencia = round((time.perf_counter() - inicio) * 1000, 2)
            return {
                "ok": False,
                "detalle": f"{type(exc).__name__}: {exc}",
                "latencia_ms": latencia,
            }

    def dispose(self) -> None:
        self._engine.dispose()

    # --- Utilidades -----------------------------------------------------
    @classmethod
    def reset(cls) -> None:
        """Descarta la instancia. Solo para tests y scripts de arranque."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.dispose()
            cls._instance = None


def get_session_manager() -> DatabaseSessionManager:
    """Dependencia de FastAPI. Siempre devuelve la misma instancia."""
    return DatabaseSessionManager()


def get_db() -> Iterator[Session]:
    """Dependencia para endpoints que necesiten una sesión."""
    with get_session_manager().session() as sesion:
        yield sesion
