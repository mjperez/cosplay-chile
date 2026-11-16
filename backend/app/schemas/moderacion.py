import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.models.enums import (
    EstadoContacto,
    EstadoReporte,
    EstadoUsuario,
    MotivoReporte,
    Rol,
    TipoContacto,
    TipoObjetoReporte,
    TipoPerfil,
)
from app.schemas.comun import AutorResumen, ModeloOrm
from app.services.moderacion_service import AccionReporte

Motivo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=1000)]


class ReporteOut(BaseModel):
    id: uuid.UUID
    tipo_objeto: TipoObjetoReporte
    objeto_id: uuid.UUID
    motivo: MotivoReporte
    detalle: str
    estado: EstadoReporte
    resolucion: str | None
    created_at: datetime
    resuelto_at: datetime | None
    reportante: AutorResumen | None
    objeto_texto: str
    objeto_enlace: str | None
    objeto_oculto: bool
    autor_objeto: AutorResumen | None
    autor_objeto_estado: EstadoUsuario | None


class ResolverReporteIn(BaseModel):
    accion: AccionReporte
    resolucion: Motivo


class UsuarioAdminOut(BaseModel):
    id: uuid.UUID
    nombre: str
    email: str
    rol: Rol
    estado: EstadoUsuario
    tipo_perfil: TipoPerfil | None
    motivo_suspension: str | None
    created_at: datetime


class SuspensionIn(BaseModel):
    motivo: Motivo


class ContactoOut(ModeloOrm):
    id: uuid.UUID
    nombre: str
    email: str
    tipo: TipoContacto
    asunto: str
    mensaje: str
    estado: EstadoContacto
    created_at: datetime


class AuditoriaOut(BaseModel):
    id: uuid.UUID
    evento: str
    actor: AutorResumen | None
    detalle: dict
    created_at: datetime


class ResumenModeracion(BaseModel):
    contenidos_pendientes: int
    eventos_pendientes: int
    reportes_abiertos: int
    contactos_nuevos: int
