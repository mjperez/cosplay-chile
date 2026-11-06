"""Esquemas de entrada y salida de autenticación."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.privacidad import VERSION as VERSION_PRIVACIDAD
from app.core.security import MAX_BYTES_PASSWORD

# Roles que una persona puede asignarse al registrarse. `administrador` queda
# fuera a propósito: si se aceptara desde el cuerpo de la petición, cualquiera
# podría crearse una cuenta con permisos de administración.
RolAutoasignable = Literal[
    "visitante",
    "cosplayer",
    "cosmaker",
    "sastre",
    "tienda",
    "fotografo",
    "organizador",
]


class RegistroEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    correo: EmailStr
    password: str = Field(min_length=8, max_length=MAX_BYTES_PASSWORD)
    rol: RolAutoasignable = "cosplayer"
    region: str = Field(min_length=2, max_length=80)
    acepta_privacidad: bool
    consentimiento_version: str = Field(min_length=1, max_length=20)

    @field_validator("password")
    @classmethod
    def no_exceder_bytes(cls, valor: str) -> str:
        if len(valor.encode("utf-8")) > MAX_BYTES_PASSWORD:
            raise ValueError(f"la contraseña no puede superar los {MAX_BYTES_PASSWORD} bytes")
        return valor

    @field_validator("acepta_privacidad")
    @classmethod
    def exigir_aceptacion(cls, valor: bool) -> bool:
        if not valor:
            raise ValueError("hay que aceptar la política de privacidad para crear la cuenta")
        return valor

    @field_validator("consentimiento_version")
    @classmethod
    def version_vigente(cls, valor: str) -> str:
        if valor != VERSION_PRIVACIDAD:
            raise ValueError(
                f"la versión vigente de la política es {VERSION_PRIVACIDAD}, se recibió {valor}"
            )
        return valor


class LoginEntrada(BaseModel):
    correo: EmailStr
    password: str = Field(min_length=1, max_length=MAX_BYTES_PASSWORD)


class UsuarioPublico(BaseModel):
    """Vista de un usuario sin datos sensibles."""

    model_config = ConfigDict(from_attributes=True)

    id_usuario: uuid.UUID
    nombre: str
    correo: EmailStr
    rol: str
    region: str
    activo: bool
    creado_en: datetime


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UsuarioPublico


class PaginaUsuarios(BaseModel):
    total: int
    limite: int
    desplazamiento: int
    elementos: list[UsuarioPublico]
