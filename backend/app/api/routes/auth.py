"""Registro, inicio de sesión y datos del usuario autenticado."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual
from app.core import privacidad
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import crear_token_acceso
from app.models.usuario import Usuario
from app.schemas.auth import (
    LoginEntrada,
    RegistroEntrada,
    TokenRespuesta,
    UsuarioPublico,
)
from app.services import auth as servicio

router = APIRouter(prefix="/auth", tags=["autenticación"])
router_privacidad = APIRouter(tags=["privacidad"])


def _ip_cliente(peticion: Request) -> str | None:
    return peticion.client.host if peticion.client else None


@router.post(
    "/registro",
    response_model=UsuarioPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una cuenta",
)
def registro(
    datos: RegistroEntrada,
    peticion: Request,
    sesion: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Usuario:
    try:
        return servicio.registrar(sesion, datos, settings)
    except servicio.CorreoYaRegistrado:
        # El registro sí revela que un correo existe. Es inevitable si se
        # quiere dar un mensaje útil, y no permite probar contraseñas.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ese correo ya tiene una cuenta",
        )


@router.post(
    "/login",
    response_model=TokenRespuesta,
    summary="Obtener un token de acceso",
)
def login(
    datos: LoginEntrada,
    peticion: Request,
    sesion: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenRespuesta:
    try:
        usuario = servicio.autenticar(
            sesion,
            correo=str(datos.correo),
            password=datos.password,
            ip=_ip_cliente(peticion),
            settings=settings,
        )
    except servicio.CuentaBloqueada as bloqueo:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="demasiados intentos fallidos, intenta más tarde",
            headers={"Retry-After": str(bloqueo.segundos)},
        )
    except (servicio.CredencialesInvalidas, servicio.CuentaInactiva):
        # Mismo mensaje para correo inexistente, contraseña incorrecta y
        # cuenta deshabilitada. Distinguirlos permitiría enumerar cuentas.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, vigencia = crear_token_acceso(
        id_usuario=usuario.id_usuario, rol=usuario.rol, settings=settings
    )
    return TokenRespuesta(
        access_token=token,
        expires_in=vigencia,
        usuario=UsuarioPublico.model_validate(usuario),
    )


@router.get(
    "/me",
    response_model=UsuarioPublico,
    summary="Datos del usuario del token",
)
def yo(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
    return usuario


@router_privacidad.get(
    "/privacidad",
    summary="Versión vigente de la política de privacidad",
)
def politica_privacidad() -> dict:
    """El cliente necesita la versión para enviarla al registrarse.

    Sin este endpoint el frontend tendría que escribir la versión a mano y se
    desincronizaría en cuanto el texto cambie.
    """
    return {
        "version": privacidad.VERSION,
        "fecha": privacidad.FECHA.isoformat(),
        "titulo": privacidad.TITULO,
        "texto": privacidad.TEXTO,
    }
