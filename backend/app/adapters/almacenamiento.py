"""Patrón Adapter (estructural) declarado en el informe ES2, sección 4.

El informe comprometió una interfaz interna `IAlmacenamientoArchivos` con
`guardar_archivo()`, `eliminar_archivo()` y `obtener_enlace()`, y un adaptador
`CloudinaryStorageAdapter` que traduzca esas operaciones a la librería externa.
Aquí están ambos, más un adaptador local para desarrollo y pruebas.

Por qué importa: los módulos de contenidos y perfiles sólo conocen la interfaz.
Migrar de disco local a Cloudinary (o a otro proveedor) se resuelve cambiando
`STORAGE_BACKEND`, sin tocar un servicio ni un endpoint. Es el principio de
inversión de dependencias que el informe pide explicitar.

Seguridad: las credenciales del proveedor se leen de `Settings` (variables de
entorno) y jamás aparecen en el código, como exige la guía OWASP, proceso 1.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Protocol

from app.core.config import Settings, get_settings

__all__ = [
    "AlmacenamientoLocalAdapter",
    "AlmacenamientoNoConfigurado",
    "ArchivoNoEncontrado",
    "ClienteCloudinaryHTTP",
    "CloudinaryStorageAdapter",
    "IAlmacenamientoArchivos",
    "obtener_almacenamiento",
]


class ArchivoNoEncontrado(Exception):
    """El adaptador no tiene el identificador solicitado."""


class AlmacenamientoNoConfigurado(Exception):
    """Faltan credenciales para el backend elegido."""


class IAlmacenamientoArchivos(ABC):
    """Interfaz interna del dominio. Es lo único que ven los servicios."""

    @abstractmethod
    def guardar_archivo(self, identificador: str, contenido: bytes) -> str:
        """Persiste el archivo y devuelve su enlace público."""

    @abstractmethod
    def eliminar_archivo(self, identificador: str) -> None:
        """Borra el archivo. Lanza `ArchivoNoEncontrado` si no existe."""

    @abstractmethod
    def obtener_enlace(self, identificador: str) -> str:
        """Devuelve la URL pública sin escribir nada."""


class AlmacenamientoLocalAdapter(IAlmacenamientoArchivos):
    """Adaptador de desarrollo: escribe en disco y sirve por `/archivos`.

    En el plan free de Render el disco es efímero; por eso producción usa el
    adaptador de nube. Para la demo local y las pruebas, éste es suficiente.
    """

    def __init__(self, directorio: Path, prefijo_url: str = "/archivos") -> None:
        self._directorio = directorio.resolve()
        self._directorio.mkdir(parents=True, exist_ok=True)
        self._prefijo_url = prefijo_url.rstrip("/")

    def _ruta(self, identificador: str) -> Path:
        ruta = (self._directorio / identificador).resolve()
        # Defensa frente a `../`: el identificador lo genera el servicio, pero
        # el DELETE lo recibe de la URL y es controlado por el cliente.
        if not ruta.is_relative_to(self._directorio):
            raise ValueError("identificador fuera del directorio permitido")
        return ruta

    def guardar_archivo(self, identificador: str, contenido: bytes) -> str:
        ruta = self._ruta(identificador)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(contenido)
        return self.obtener_enlace(identificador)

    def eliminar_archivo(self, identificador: str) -> None:
        ruta = self._ruta(identificador)
        if not ruta.is_file():
            raise ArchivoNoEncontrado(identificador)
        ruta.unlink()

    def obtener_enlace(self, identificador: str) -> str:
        return f"{self._prefijo_url}/{identificador}"


class ClienteNube(Protocol):
    """Lo mínimo que el adaptador espera del SDK/HTTP del proveedor."""

    cloud_name: str

    def subir(self, public_id: str, contenido: bytes) -> str: ...

    def borrar(self, public_id: str) -> None: ...


class CloudinaryStorageAdapter(IAlmacenamientoArchivos):
    """Traduce la interfaz interna a las operaciones del proveedor externo.

    El cliente se inyecta: en producción es `ClienteCloudinaryHTTP`, y en las
    pruebas un doble en memoria. Así se verifica la traducción sin red ni
    credenciales, y el adaptador sigue siendo sustituible por otro proveedor.
    """

    def __init__(
        self, cliente: ClienteNube, carpeta: str = "cosplay-chile"
    ) -> None:
        self._cliente = cliente
        self._carpeta = carpeta.strip("/")

    def _public_id(self, identificador: str) -> str:
        sin_extension = identificador.rsplit(".", 1)[0]
        return f"{self._carpeta}/{sin_extension}"

    def guardar_archivo(self, identificador: str, contenido: bytes) -> str:
        return self._cliente.subir(self._public_id(identificador), contenido)

    def eliminar_archivo(self, identificador: str) -> None:
        self._cliente.borrar(self._public_id(identificador))

    def obtener_enlace(self, identificador: str) -> str:
        public_id = urllib.parse.quote(self._public_id(identificador), safe="/")
        return (
            f"https://res.cloudinary.com/{self._cliente.cloud_name}"
            f"/image/upload/{public_id}"
        )


class ClienteCloudinaryHTTP:
    """Cliente HTTP real de Cloudinary, sin librerías de terceros.

    Firma las peticiones con SHA-1 (`timestamp` + parámetros + api_secret) y
    envía el binario como multipart. `abrir` es inyectable para poder probar
    la construcción de la petición sin salir a internet.
    """

    BASE = "https://api.cloudinary.com/v1_1/{cloud}/image/{accion}"

    def __init__(
        self,
        cloud_name: str,
        api_key: str,
        api_secret: str,
        abrir: Callable[..., Any] | None = None,
    ) -> None:
        self.cloud_name = cloud_name
        self._api_key = api_key
        self._api_secret = api_secret
        self._abrir = abrir or urllib.request.urlopen

    def _firmar(self, parametros: dict[str, str]) -> str:
        cadena = "&".join(f"{k}={parametros[k]}" for k in sorted(parametros))
        return hashlib.sha1(
            (cadena + self._api_secret).encode("utf-8")
        ).hexdigest()

    def _enviar(
        self, accion: str, campos: dict[str, str], contenido: bytes | None = None
    ) -> dict:
        campos = {**campos, "api_key": self._api_key}
        campos["signature"] = self._firmar(campos)
        limite = f"----cosplay{uuid.uuid4().hex}"
        partes: list[bytes] = []
        for clave, valor in campos.items():
            partes.append(
                f"--{limite}\r\nContent-Disposition: form-data; name=\"{clave}\"\r\n\r\n"
                f"{valor}\r\n".encode()
            )
        if contenido is not None:
            partes.append(
                f"--{limite}\r\nContent-Disposition: form-data; name=\"file\"; "
                "filename=\"archivo\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
                + contenido
                + b"\r\n"
            )
        partes.append(f"--{limite}--\r\n".encode())
        peticion = urllib.request.Request(
            self.BASE.format(cloud=self.cloud_name, accion=accion),
            data=b"".join(partes),
            headers={"Content-Type": f"multipart/form-data; boundary={limite}"},
            method="POST",
        )
        with self._abrir(peticion, timeout=20) as respuesta:
            return json.loads(respuesta.read().decode())

    def subir(self, public_id: str, contenido: bytes) -> str:
        respuesta = self._enviar(
            "upload",
            {"public_id": public_id, "timestamp": str(int(time.time()))},
            contenido,
        )
        return respuesta["secure_url"]

    def borrar(self, public_id: str) -> None:
        respuesta = self._enviar(
            "destroy", {"public_id": public_id, "timestamp": str(int(time.time()))}
        )
        if respuesta.get("result") != "ok":
            raise ArchivoNoEncontrado(public_id)


def obtener_almacenamiento(settings: Settings | None = None) -> IAlmacenamientoArchivos:
    """Fábrica del adaptador según `STORAGE_BACKEND`.

    Es el único punto que conoce los adaptadores concretos; los servicios
    reciben la interfaz por inyección de dependencias.
    """
    config = settings or get_settings()
    if config.storage_backend.lower() == "cloudinary":
        credenciales = (
            config.cloudinary_cloud_name,
            config.cloudinary_api_key,
            config.cloudinary_api_secret,
        )
        if not all(credenciales):
            raise AlmacenamientoNoConfigurado(
                "STORAGE_BACKEND=cloudinary requiere CLOUDINARY_CLOUD_NAME, "
                "CLOUDINARY_API_KEY y CLOUDINARY_API_SECRET"
            )
        cliente = ClienteCloudinaryHTTP(*credenciales)  # type: ignore[arg-type]
        return CloudinaryStorageAdapter(cliente)
    return AlmacenamientoLocalAdapter(Path(config.storage_directorio))
