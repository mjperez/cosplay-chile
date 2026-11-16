"""Dependencias de FastAPI: sesión de BD, usuario actual y control de rol."""
import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decodificar_token
from app.db.session_manager import get_db
from app.models.enums import EstadoUsuario, Rol
from app.models.usuario import Usuario
from app.patterns.observer import GestorEventos, get_gestor_eventos

DbSession = Annotated[AsyncSession, Depends(get_db)]
Gestor = Annotated[GestorEventos, Depends(get_gestor_eventos)]

_bearer = HTTPBearer(auto_error=False, description="Token JWT obtenido en /api/auth/login")

SESION_REQUERIDA = "Debes iniciar sesión para realizar esta acción"
SESION_EXPIRADA = "Tu sesión expiró. Vuelve a iniciar sesión"


def _no_autorizado(detalle: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detalle, headers={"WWW-Authenticate": "Bearer"})


async def _usuario_desde_token(db: AsyncSession, cred: HTTPAuthorizationCredentials | None) -> Usuario | None:
    if cred is None:
        return None
    try:
        payload = decodificar_token(cred.credentials)
        usuario_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise _no_autorizado(SESION_EXPIRADA)
    usuario = await db.get(Usuario, usuario_id)
    if usuario is None or usuario.estado == EstadoUsuario.ELIMINADO:
        raise _no_autorizado(SESION_EXPIRADA)
    if usuario.estado == EstadoUsuario.SUSPENDIDO:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            {"codigo": "CUENTA_SUSPENDIDA", "mensaje": "Tu cuenta no está habilitada."},
        )
    return usuario


async def get_usuario_actual(
    db: DbSession, cred: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> Usuario:
    usuario = await _usuario_desde_token(db, cred)
    if usuario is None:
        raise _no_autorizado(SESION_REQUERIDA)
    return usuario


async def get_usuario_opcional(
    db: DbSession, cred: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> Usuario | None:
    """Para rutas públicas que muestran algo extra si hay sesión (p. ej. favoritos)."""
    try:
        return await _usuario_desde_token(db, cred)
    except HTTPException:
        return None


async def requiere_admin(usuario: Annotated[Usuario, Depends(get_usuario_actual)]) -> Usuario:
    if usuario.rol != Rol.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el equipo de moderación puede realizar esta acción")
    return usuario


UsuarioActual = Annotated[Usuario, Depends(get_usuario_actual)]
UsuarioOpcional = Annotated[Usuario | None, Depends(get_usuario_opcional)]
Admin = Annotated[Usuario, Depends(requiere_admin)]
