"""Configuración de la aplicación leída desde variables de entorno.

Ningún valor sensible vive en el repositorio. `.env` está en `.gitignore` y en
Render las variables se cargan desde el panel del servicio.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def normalizar_dsn(valor: str) -> str:
    """Fuerza un driver explícito en el DSN.

    SQLAlchemy 2.0 rechaza el esquema `postgres://` que todavía entregan
    algunos proveedores, y sin driver explícito intenta psycopg2. Fijamos
    psycopg 3 para que el DSN sea el mismo en local, en Supabase y en Render.
    """
    if valor.startswith("postgres://"):
        return valor.replace("postgres://", "postgresql+psycopg://", 1)
    if valor.startswith("postgresql://"):
        return valor.replace("postgresql://", "postgresql+psycopg://", 1)
    return valor


class Settings(BaseSettings):
    """Parámetros de ejecución del servicio.

    Todos los campos sin valor por defecto son obligatorios: si falta la
    variable de entorno, el proceso falla al arrancar en lugar de arrancar
    con una configuración a medias.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Aplicación -----------------------------------------------------
    app_name: str = "cosplay-chile-api"
    environment: str = "local"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # --- Base de datos --------------------------------------------------
    database_url: str = Field(
        ...,
        description="DSN de PostgreSQL. Neon entrega 'postgresql://...'; "
        "el validador agrega el driver de SQLAlchemy.",
    )
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    db_echo: bool = False

    # --- Seguridad ------------------------------------------------------
    jwt_secret: str = Field(..., min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    # Costo de bcrypt. 12 es el valor de producción; las pruebas lo bajan a 4
    # para no gastar 250 ms por cada hash.
    bcrypt_rounds: int = Field(default=12, ge=4, le=16)

    # --- CORS -----------------------------------------------------------
    # NoDecode evita que pydantic-settings intente interpretar el valor como
    # JSON antes de validarlo. El campo acepta lista, JSON o texto separado
    # por comas, que es lo que suele quedar cuando se copia una URL.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parsear_origenes(cls, valor: object) -> object:
        if isinstance(valor, str):
            texto = valor.strip()
            if texto.startswith("["):
                return json.loads(texto)
            return [origen.strip() for origen in texto.split(",") if origen.strip()]
        return valor

    @field_validator("database_url")
    @classmethod
    def normalizar(cls, valor: str) -> str:
        return normalizar_dsn(valor)

    @property
    def es_produccion(self) -> bool:
        return self.environment.lower() in {"production", "produccion"}


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración una sola vez por proceso.

    El caché evita releer el entorno en cada request y permite que los tests
    lo limpien con `get_settings.cache_clear()`.
    """
    return Settings()
