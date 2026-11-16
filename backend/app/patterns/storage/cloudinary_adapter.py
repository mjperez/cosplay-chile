"""Adaptador hacia Cloudinary: traduce la interfaz interna a la API propietaria del SDK.

No se usa por defecto en el prototipo. Para activarlo: ``pip install cloudinary``,
STORAGE_BACKEND=cloudinary y CLOUDINARY_URL=cloudinary://key:secret@cloud.
El SDK se importa de forma diferida para que no sea dependencia obligatoria.
"""
import asyncio
import io

from app.patterns.storage.interfaz import IAlmacenamientoArchivos


class CloudinaryStorageAdapter(IAlmacenamientoArchivos):
    def __init__(self, cloudinary_url: str, carpeta: str = "cosplaychile", sdk=None) -> None:
        if sdk is None:
            try:
                import cloudinary  # type: ignore
                import cloudinary.uploader  # type: ignore  # noqa: F401
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("Instala el paquete 'cloudinary' para usar este adaptador") from exc
            cloudinary.config(cloudinary_url=cloudinary_url, secure=True)
            sdk = cloudinary
        self._sdk = sdk
        self._carpeta = carpeta

    def _public_id(self, clave: str) -> str:
        return clave.rsplit(".", 1)[0]

    async def guardar_archivo(self, contenido: bytes, nombre: str, content_type: str) -> str:
        public_id = f"{self._carpeta}/{self._public_id(nombre)}"
        await asyncio.to_thread(
            self._sdk.uploader.upload, io.BytesIO(contenido), public_id=public_id, resource_type="image"
        )
        return public_id

    async def eliminar_archivo(self, clave: str) -> None:
        await asyncio.to_thread(self._sdk.uploader.destroy, clave, resource_type="image")

    def obtener_enlace(self, clave: str) -> str:
        url, _ = self._sdk.utils.cloudinary_url(clave, secure=True)
        return url
