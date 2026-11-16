"""Patrón Singleton: DatabaseSessionManager (informe, pág. 29 y Fig. 12).

Garantiza un único motor async y un único pool de conexiones durante todo el
ciclo de vida de la aplicación. Los controladores NO crean conexiones: piden una
sesión mediante la dependencia ``get_db`` (inyección de dependencias de FastAPI),
que la obtiene de esta instancia única.
"""
from __future__ import annotations

import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseSessionManager:
    _instancia: "DatabaseSessionManager | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "DatabaseSessionManager":
        # Doble verificación con lock: aunque se llame desde varios hilos,
        # solo se construye una instancia.
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    instancia = super().__new__(cls)
                    instancia._engine = None
                    instancia._sessionmaker = None
                    cls._instancia = instancia
        return cls._instancia

    # --- ciclo de vida -------------------------------------------------
    def init(self, database_url: str, **engine_kwargs) -> None:
        """Crea el motor y el pool. Es idempotente: si ya existe, no hace nada."""
        if self._engine is not None:
            return
        opciones = {"pool_pre_ping": True}
        if "poolclass" not in engine_kwargs:
            # Pool acotado: async + reutilización de conexiones (RNF-04)
            opciones.update(pool_size=10, max_overflow=20)
        opciones.update(engine_kwargs)
        self._engine = create_async_engine(database_url, **opciones)
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @property
    def inicializado(self) -> bool:
        return self._engine is not None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager no inicializado")
        return self._engine

    # --- acceso a sesiones --------------------------------------------
    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Entrega una sesión del pool compartido; hace rollback si algo falla."""
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager no inicializado")
        sesion = self._sessionmaker()
        try:
            yield sesion
        except Exception:
            await sesion.rollback()
            raise
        finally:
            await sesion.close()

    # Nombre usado en el diagrama de secuencia (Fig. 12)
    obtener_conexion = session


async def get_db() -> AsyncIterator[AsyncSession]:
    """Dependencia de FastAPI: una sesión por petición, tomada del Singleton."""
    async with DatabaseSessionManager().session() as sesion:
        yield sesion
