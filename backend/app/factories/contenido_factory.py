"""Factory Method para la creación de contenido editorial (US-08).

El patrón
---------
`CreadorContenido` es el creador abstracto. Declara `construir`, que es el
Factory Method: cada subclase decide qué producto concreto instanciar
(`GuiaTutorial`, `Entrevista` o `Articulo`). El método `crear` es la parte que
no varía: aplica las reglas comunes a cualquier contenido (autor, tipo y estado
inicial en borrador) sobre lo que devuelve el Factory Method.

Por qué así y no un `if` en el endpoint: agregar un cuarto tipo de contenido
significa escribir una subclase de creador y registrarla. No hay que tocar el
endpoint, ni el servicio, ni las reglas de estado. El endpoint no sabe qué
clases existen.

Nota sobre el tipo: se asigna explícitamente en `crear` aunque SQLAlchemy
también lo derive del `polymorphic_identity`. Sin eso, el atributo queda vacío
hasta el flush y la respuesta HTTP saldría sin `tipo`.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import ClassVar

from app.models.contenido import Articulo, Contenido, Entrevista, GuiaTutorial
from app.schemas.contenido import (
    ArticuloEntrada,
    ContenidoEntrada,
    EntrevistaEntrada,
    GuiaEntrada,
)


class TipoContenidoInvalido(Exception):
    def __init__(self, tipo: str) -> None:
        self.tipo = tipo
        super().__init__(f"tipo de contenido desconocido: {tipo}")


class CreadorContenido(ABC):
    """Creador del patrón Factory Method."""

    tipo: ClassVar[str]

    @abstractmethod
    def construir(self, datos: ContenidoEntrada) -> Contenido:
        """Factory Method: devuelve la subclase concreta, sin persistirla."""

    def crear(self, datos: ContenidoEntrada, id_autor: uuid.UUID) -> Contenido:
        """Método plantilla con las reglas comunes a todo contenido."""
        contenido = self.construir(datos)
        contenido.id_autor = id_autor
        contenido.tipo = self.tipo
        # Un contenido nace en borrador. Publicarlo es una acción aparte, y
        # solo la puede ejecutar un administrador.
        contenido.estado = "pendiente"
        return contenido

    @staticmethod
    def _comunes(datos: ContenidoEntrada) -> dict:
        return {
            "titulo": datos.titulo,
            "resumen": datos.resumen,
            "nivel": datos.nivel,
            "id_categoria": datos.id_categoria,
            "cuerpo": datos.cuerpo,
            "imagenes": [str(url) for url in datos.imagenes] if datos.imagenes else None,
            "video_url": datos.video_url,
        }


class CreadorGuia(CreadorContenido):
    tipo = "guia"

    def construir(self, datos: GuiaEntrada) -> GuiaTutorial:
        return GuiaTutorial(
            **self._comunes(datos),
            personaje=datos.personaje,
            medidas=[medida.model_dump() for medida in datos.medidas] if datos.medidas else None,
            tecnicas=datos.tecnicas,
            presupuesto=datos.presupuesto,
            seguridad=datos.seguridad,
            pasos=datos.pasos,
            materiales=datos.materiales,
        )


class CreadorEntrevista(CreadorContenido):
    tipo = "entrevista"

    def construir(self, datos: EntrevistaEntrada) -> Entrevista:
        return Entrevista(
            **self._comunes(datos),
            preguntas=datos.preguntas,
            respuestas=datos.respuestas,
        )


class CreadorArticulo(CreadorContenido):
    tipo = "articulo"

    def construir(self, datos: ArticuloEntrada) -> Articulo:
        return Articulo(
            **self._comunes(datos),
            enlaces=[str(url) for url in datos.enlaces] if datos.enlaces else None,
        )


class ContenidoFactory:
    """Registro de creadores. Resuelve el tipo y delega."""

    _creadores: ClassVar[dict[str, type[CreadorContenido]]] = {
        creador.tipo: creador
        for creador in (CreadorGuia, CreadorEntrevista, CreadorArticulo)
    }

    @classmethod
    def para(cls, tipo: str) -> CreadorContenido:
        creador = cls._creadores.get(tipo)
        if creador is None:
            raise TipoContenidoInvalido(tipo)
        return creador()

    @classmethod
    def crear(cls, datos: ContenidoEntrada, id_autor: uuid.UUID) -> Contenido:
        return cls.para(datos.tipo).crear(datos, id_autor)

    @classmethod
    def tipos(cls) -> tuple[str, ...]:
        return tuple(cls._creadores)
