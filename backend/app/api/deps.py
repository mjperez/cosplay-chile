"""Dependencias de FastAPI: sesión, usuario actual y control de roles."""

from __future__ import annotations

import uuid
from typing import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import decodificar_token
from app.models.usuario import Usuario
from app.repositories import usuario as repo_usuarios

esquema_bearer = HTTPBearer(auto_error=False, description="Token JWT en el header Authorization")

NO_AUTENTICADO = {"WWW-Authenticate": "Bearer"}


def _no_autorizado(detalle: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalle,
        headers=NO_AUTENTICADO,
    )


def get_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    sesion: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Usuario:
    """Resuelve el usuario a partir del token. Falla con 401 si no es válido."""
    if credenciales is None:
        raise _no_autorizado("falta el token de acceso")

    try:
        payload = decodificar_token(credenciales.credentials, settings)
    except jwt.ExpiredSignatureError:
        raise _no_autorizado("el token expiró")
    except jwt.InvalidTokenError:
        raise _no_autorizado("el token no es válido")

    try:
        id_usuario = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError):
        raise _no_autorizado("el token no es válido")

    usuario = repo_usuarios.obtener_por_id(sesion, id_usuario)
    if usuario is None or not usuario.activo:
        raise _no_autorizado("el token no es válido")

    return usuario


def requiere_roles(*roles: str) -> Callable[..., Usuario]:
    """Devuelve una dependencia que exige que el usuario tenga uno de los roles.

    Se usa como `Depends(requiere_roles("administrador"))`. Un usuario con otro
    rol recibe 403, no 401: está autenticado, no autorizado.
    """

    def dependencia(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="no tienes permisos para esta operación",
            )
        return usuario

    return dependencia


requiere_admin = requiere_roles("administrador")
