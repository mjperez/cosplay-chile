"""Importa todos los modelos para que queden registrados en Base.metadata (Alembic)."""
from app.models.comunidad import DesafioMensual, Foro, ParticipacionDesafio, Respuesta, Tema
from app.models.contenido import ArticuloTecnico, CategoriaContenido, Contenido, Entrevista, GuiaTutorial
from app.models.directorio import ComunidadGrupo, DirectorioItem, ProveedorServicio, Resena, Tienda
from app.models.evento import Evento, ParticipacionEvento
from app.models.interaccion import Contacto, Favorito, Notificacion, RegistroAuditoria, Reporte
from app.models.usuario import Perfil, TokenRecuperacion, Usuario

__all__ = [
    "ArticuloTecnico", "CategoriaContenido", "ComunidadGrupo", "Contacto", "Contenido",
    "DesafioMensual", "DirectorioItem", "Entrevista", "Evento", "Favorito", "Foro", "GuiaTutorial",
    "Notificacion", "ParticipacionDesafio", "ParticipacionEvento", "Perfil", "ProveedorServicio",
    "RegistroAuditoria", "Reporte", "Resena", "Respuesta", "Tema", "Tienda", "TokenRecuperacion",
    "Usuario",
]
