"""Subida de imágenes vía el Adapter IAlmacenamientoArchivos (UC6 excepción 2: límite de tamaño)."""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.deps import UsuarioActual
from app.patterns.storage import IAlmacenamientoArchivos, get_storage

router = APIRouter(prefix="/api/archivos", tags=["Archivos"])

# Se identifica el tipo por su firma binaria, no por la extensión que manda el cliente
FIRMAS = {
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
}


def detectar_imagen(contenido: bytes) -> tuple[str, str] | None:
    for firma, tipo in FIRMAS.items():
        if contenido.startswith(firma):
            return tipo
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return ("webp", "image/webp")
    return None


class ArchivoOut(BaseModel):
    clave: str
    url: str


@router.post("", response_model=ArchivoOut, status_code=status.HTTP_201_CREATED,
             summary="Subir una imagen (JPG, PNG o WebP)")
async def subir_imagen(
    usuario: UsuarioActual,
    storage: Annotated[IAlmacenamientoArchivos, Depends(get_storage)],
    archivo: UploadFile = File(...),
):
    limite_mb = get_settings().max_upload_mb
    limite = limite_mb * 1024 * 1024
    contenido = await archivo.read(limite + 1)
    if len(contenido) > limite:
        raise HTTPException(
            413,
            f"El archivo supera el tamaño máximo permitido de {limite_mb} MB.",
        )
    tipo = detectar_imagen(contenido)
    if tipo is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Solo se aceptan imágenes JPG, PNG o WebP.")
    extension, content_type = tipo
    nombre = f"subidas/{datetime.now(timezone.utc):%Y%m}/{uuid.uuid4().hex}.{extension}"
    clave = await storage.guardar_archivo(contenido, nombre, content_type)
    return ArchivoOut(clave=clave, url=storage.obtener_enlace(clave))
