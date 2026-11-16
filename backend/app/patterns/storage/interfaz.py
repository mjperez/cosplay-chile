"""Patrón Adapter (informe, págs. 30-31): interfaz interna de almacenamiento.

Los módulos de portafolios, tutoriales y foro dependen solo de esta interfaz,
nunca de una librería de terceros (principio de inversión de dependencias).
"""
from abc import ABC, abstractmethod


class IAlmacenamientoArchivos(ABC):
    @abstractmethod
    async def guardar_archivo(self, contenido: bytes, nombre: str, content_type: str) -> str:
        """Guarda el archivo y devuelve su clave (identificador interno)."""

    @abstractmethod
    async def eliminar_archivo(self, clave: str) -> None:
        """Elimina el archivo identificado por la clave (no falla si no existe)."""

    @abstractmethod
    def obtener_enlace(self, clave: str) -> str:
        """URL pública con la que el frontend muestra el archivo."""
