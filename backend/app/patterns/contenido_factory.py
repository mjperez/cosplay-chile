"""Patrón Factory Method (informe, págs. 29-30; Fig. 13 «GestorContenido (Factory)»).

``ContenidoFactory.crear_contenido(tipo, datos)`` evalúa el tipo y crea la
subclase concreta de ``Contenido`` (GuiaTutorial, Entrevista o ArticuloTecnico),
que aplica su propia validación antes de guardarse. Los controladores no
conocen las clases concretas: para sumar un formato nuevo basta con registrarlo.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contenido import (
    ArticuloTecnico,
    CategoriaContenido,
    Contenido,
    ContenidoInvalido,
    Entrevista,
    GuiaTutorial,
)
from app.models.enums import EstadoPublicacion, TipoContenido


class CategoriaNoEncontrada(LookupError):
    """Flujo alterno 4a de UC6."""
    mensaje = "Categoría no encontrada"


class TipoContenidoDesconocido(ValueError):
    pass


class ContenidoFactory:
    _tipos: dict[TipoContenido, type[Contenido]] = {
        TipoContenido.GUIA: GuiaTutorial,
        TipoContenido.ENTREVISTA: Entrevista,
        TipoContenido.ARTICULO: ArticuloTecnico,
    }

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @classmethod
    def registrar_tipo(cls, tipo: TipoContenido, clase: type[Contenido]) -> None:
        """Punto de extensión: nuevos formatos sin tocar controladores."""
        cls._tipos[tipo] = clase

    @classmethod
    def tipos_disponibles(cls) -> list[TipoContenido]:
        return list(cls._tipos)

    async def validar_categoria(self, categoria_id: Any) -> CategoriaContenido:
        """validarCategoria(categoriaId) de la Fig. 13."""
        try:
            cid = categoria_id if isinstance(categoria_id, uuid.UUID) else uuid.UUID(str(categoria_id))
        except (TypeError, ValueError):
            raise CategoriaNoEncontrada()
        categoria = await self.db.get(CategoriaContenido, cid)
        if categoria is None:
            raise CategoriaNoEncontrada()
        return categoria

    async def crear_contenido(self, tipo: str | TipoContenido, datos: dict[str, Any]) -> Contenido:
        """Valida la categoría, instancia la subclase y la guarda en estado PENDIENTE."""
        try:
            clase = self._tipos[TipoContenido(tipo)]
        except (KeyError, ValueError):
            raise TipoContenidoDesconocido(f"Tipo de contenido no soportado: {tipo}")

        categoria = await self.validar_categoria(datos.get("categoria_id"))

        contenido = clase()
        contenido.asignar_datos_comunes(datos)
        contenido.cargar_datos_propios(datos)
        contenido.validar()  # reglas específicas de cada subclase (polimorfismo)

        contenido.categoria = categoria
        contenido.autor_id = datos["autor_id"]
        contenido.estado = EstadoPublicacion.PENDIENTE  # nace pendiente de revisión
        self.db.add(contenido)
        await self.db.flush()
        return contenido


__all__ = ["CategoriaNoEncontrada", "ContenidoFactory", "ContenidoInvalido", "TipoContenidoDesconocido"]
