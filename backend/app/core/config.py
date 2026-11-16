"""Configuración leída de variables de entorno (sin secretos en el código)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://cosplay:cosplay@localhost:5432/cosplay"
    test_database_url: str = "postgresql+asyncpg://cosplay:cosplay@localhost:5432/cosplay_test"

    jwt_secret: str
    jwt_algoritmo: str = "HS256"
    jwt_expira_minutos: int = 60
    recuperacion_expira_minutos: int = 30

    frontend_url: str = "http://localhost:5173"
    cors_origenes_extra: str = ""

    storage_backend: str = "local"
    media_dir: str = "media"
    max_upload_mb: int = 5
    cloudinary_url: str = ""

    correo_moderacion: str = "moderacion@cosplaychile.cl"

    @property
    def media_path(self) -> Path:
        p = Path(self.media_dir)
        return p if p.is_absolute() else BACKEND_DIR / p

    @property
    def cors_origenes(self) -> list[str]:
        extra = [o.strip() for o in self.cors_origenes_extra.split(",") if o.strip()]
        return [self.frontend_url, *extra]


@lru_cache
def get_settings() -> Settings:
    return Settings()
