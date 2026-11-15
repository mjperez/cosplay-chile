"""Reglas de negocio de la subida de imágenes (RF-18, RF-27, RF-08).

La validación no confía en el `Content-Type` que declara el cliente: comprueba
la firma binaria del archivo (magic bytes) contra una **lista blanca** de
formatos. Es la aplicación directa del control OWASP A03 que pide la guía de
verificación de seguridad. Tampoco se conserva el nombre original, que es
vectores de path traversal; el identificador se genera con UUID.
"""

from __future__ import annotations

import uuid

from app.adapters.almacenamiento import IAlmacenamientoArchivos
from app.schemas.archivo import ArchivoPublico

__all__ = [
    "ArchivoDemasiadoGrande",
    "ArchivoVacio",
    "ContenidoNoCoincide",
    "TipoNoPermitido",
    "TIPOS_PERMITIDOS",
    "eliminar",
    "guardar",
    "nuevo_identificador",
]

TIPOS_PERMITIDOS: dict[str, str] = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}
TAMANO_MAXIMO = 5 * 1024 * 1024


class TipoNoPermitido(Exception):
    def __init__(self, tipo_mime: str) -> None:
        self.tipo_mime = tipo_mime
        super().__init__(f"tipo de archivo no permitido: {tipo_mime}")


class ContenidoNoCoincide(Exception):
    """El Content-Type declara una imagen, pero los bytes dicen otra cosa."""


class ArchivoVacio(Exception):
    pass


class ArchivoDemasiadoGrande(Exception):
    pass


def _coincide(contenido: bytes, tipo_mime: str) -> bool:
    if tipo_mime == "image/png":
        return contenido.startswith(b"\x89PNG\r\n\x1a\n")
    if tipo_mime == "image/jpeg":
        return contenido.startswith(b"\xff\xd8\xff")
    if tipo_mime == "image/webp":
        return contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP"
    return False


def nuevo_identificador(id_usuario: uuid.UUID, extension: str) -> str:
    """El prefijo con el dueño permite autorizar el borrado sin otra tabla."""
    return f"{id_usuario}/{uuid.uuid4().hex}.{extension}"


def guardar(
    almacenamiento: IAlmacenamientoArchivos,
    contenido: bytes,
    tipo_mime: str,
    id_usuario: uuid.UUID,
) -> ArchivoPublico:
    if tipo_mime not in TIPOS_PERMITIDOS:
        raise TipoNoPermitido(tipo_mime)
    if not contenido:
        raise ArchivoVacio()
    if len(contenido) > TAMANO_MAXIMO:
        raise ArchivoDemasiadoGrande()
    if not _coincide(contenido, tipo_mime):
        raise ContenidoNoCoincide()

    identificador = nuevo_identificador(id_usuario, TIPOS_PERMITIDOS[tipo_mime])
    enlace = almacenamiento.guardar_archivo(identificador, contenido)
    return ArchivoPublico(
        identificador=identificador,
        enlace=enlace,
        tipo_mime=tipo_mime,
        tamano=len(contenido),
    )


def eliminar(
    almacenamiento: IAlmacenamientoArchivos, identificador: str
) -> None:
    almacenamiento.eliminar_archivo(identificador)
