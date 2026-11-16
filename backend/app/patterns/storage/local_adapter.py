"""Adaptador por defecto del prototipo: guarda en disco (backend/media) y se sirve en /media."""
import asyncio
import re
from pathlib import Path

from app.patterns.storage.interfaz import IAlmacenamientoArchivos

_CLAVE_VALIDA = re.compile(r"^[A-Za-z0-9_\-/]+\.[a-z0-9]{2,5}$")


class LocalStorageAdapter(IAlmacenamientoArchivos):
    def __init__(self, directorio: Path, url_base: str = "/media") -> None:
        self.directorio = Path(directorio)
        self.url_base = url_base.rstrip("/")
        self.directorio.mkdir(parents=True, exist_ok=True)

    def _ruta(self, clave: str) -> Path:
        # Evita path traversal: la clave la genera el sistema, pero se valida igual
        if not _CLAVE_VALIDA.match(clave) or ".." in clave:
            raise ValueError("Clave de archivo inválida")
        return self.directorio / clave

    async def guardar_archivo(self, contenido: bytes, nombre: str, content_type: str) -> str:
        ruta = self._ruta(nombre)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(ruta.write_bytes, contenido)
        return nombre

    async def eliminar_archivo(self, clave: str) -> None:
        ruta = self._ruta(clave)
        await asyncio.to_thread(ruta.unlink, True)

    def obtener_enlace(self, clave: str) -> str:
        return f"{self.url_base}/{clave}"
