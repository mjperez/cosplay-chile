from functools import lru_cache

from app.core.config import get_settings
from app.patterns.storage.cloudinary_adapter import CloudinaryStorageAdapter
from app.patterns.storage.interfaz import IAlmacenamientoArchivos
from app.patterns.storage.local_adapter import LocalStorageAdapter


@lru_cache
def get_storage() -> IAlmacenamientoArchivos:
    """Elige el adaptador según STORAGE_BACKEND. El resto del sistema no se entera."""
    s = get_settings()
    if s.storage_backend == "cloudinary":
        return CloudinaryStorageAdapter(s.cloudinary_url)
    return LocalStorageAdapter(s.media_path)


__all__ = ["CloudinaryStorageAdapter", "IAlmacenamientoArchivos", "LocalStorageAdapter", "get_storage"]
