"""Modelos de datos. Importar aquí garantiza que Alembic vea todo el metadata."""

from app.models.base import Base
from app.models.comunidad import DesafioMensual, ForoRespuesta, ForoTema
from app.models.contenido import (
    Articulo,
    CategoriaContenido,
    Contenido,
    Entrevista,
    GuiaTutorial,
)
from app.models.directorio import ComunidadGrupo, DondeComprar, Proveedor
from app.models.evento import EventoCosplay, ParticipacionEvento
from app.models.intento_login import IntentoLogin
from app.models.usuario import PerfilCosplayer, Usuario

__all__ = [
    "Articulo",
    "Base",
    "CategoriaContenido",
    "ComunidadGrupo",
    "Contenido",
    "DesafioMensual",
    "DondeComprar",
    "Entrevista",
    "EventoCosplay",
    "ForoRespuesta",
    "ForoTema",
    "GuiaTutorial",
    "IntentoLogin",
    "ParticipacionEvento",
    "PerfilCosplayer",
    "Proveedor",
    "Usuario",
]
